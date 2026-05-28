from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Component, UserProfile, Configuration, ForumCategory, ForumTopic, ForumReply, ForumUpvote
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from datetime import datetime
from functools import wraps
import os
from sqlalchemy.exc import PendingRollbackError
from flask import send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import text

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    # Cache letiltása minden válasznál
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # Error handler a tranzakciós hibákhoz
    @app.errorhandler(PendingRollbackError)
    def handle_sqlalchemy_error(e):
        db.session.rollback()
        return redirect(request.url)

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = ''
    # Az App Password-öt kell használni, amit a Google Fiók beállításokban lehet generálni
    app.config['MAIL_PASSWORD'] = ''
    mail = Mail(app)

    # Konfiguráljuk a feltöltési mappát
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Profilkép elérési útvonal ellenőrzése
    def get_profile_image_path(filename):
        if not filename:
            return None
        return os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Profilkép létezésének ellenőrzése
    def check_profile_image(user):
        if user and user.profile and user.profile.profile_image:
            image_path = get_profile_image_path(user.profile.profile_image)
            if not image_path or not os.path.exists(image_path):
                user.profile.profile_image = None
                db.session.commit()

    # Komponensek lekérése API
    @app.route('/api/components', methods=['GET'])
    def get_components():
        try:
            category = request.args.get('category', '')
            manufacturer = request.args.get('manufacturer', '')
            socket = request.args.get('socket', '')
            form_factor = request.args.get('form_factor', '')
            rgb = request.args.get('rgb', '')
            type_filter = request.args.get('type', '')
            memory_type = request.args.get('memory_type', '')
            efficiency = request.args.get('efficiency', '')
            modular = request.args.get('modular', '')
            fan_size = request.args.get('fan_size', '')

            query = "SELECT * FROM components WHERE 1=1"
            params = {}

            if category:
                query += " AND category = :category"
                params["category"] = category

            if manufacturer:
                query += " AND manufacturer = :manufacturer"
                params["manufacturer"] = manufacturer

            if socket:
                query += " AND JSON_EXTRACT(attributes, '$.Foglalat') = :socket"
                params["socket"] = socket

            if form_factor:
                query += " AND JSON_EXTRACT(attributes, '$.Típus') = :form_factor"
                params["form_factor"] = form_factor

            if rgb:
                query += " AND JSON_EXTRACT(attributes, '$.RGB') = :rgb"
                params["rgb"] = rgb

            if type_filter:
                query += " AND JSON_EXTRACT(attributes, '$.Típus') = :type"
                params["type"] = type_filter

            if memory_type:
                query += " AND JSON_EXTRACT(attributes, '$.Foglalat') = :memory_type"
                params["memory_type"] = memory_type

            if efficiency:
                query += " AND JSON_EXTRACT(attributes, '$.Fogyasztás') = :efficiency"
                params["efficiency"] = efficiency

            if modular:
                query += " AND JSON_EXTRACT(attributes, '$.Modularitás') = :modular"
                params["modular"] = modular

            if fan_size:
                query += " AND JSON_EXTRACT(attributes, '$.Méret') = :fan_size"
                params["fan_size"] = fan_size

            result = db.session.execute(text(query), params)
            components = [dict(row) for row in result.mappings()]
            return jsonify(components)

        except Exception as e:
            app.logger.error(f"Error in get_components: {str(e)}")
            return jsonify({'error': 'Hiba történt az adatok lekérése során!'}), 500

    # Konfiguráció beküldése
    @app.route('/send_summary', methods=['POST'])
    @login_required
    def send_summary():
        try:
            # Ellenőrizzük, hogy a felhasználó be van-e jelentkezve
            user = User.query.get(session['user_id'])
            if not user:
                return jsonify({'error': 'Felhasználó nem található!'}), 404

            if not user.profile:
                return jsonify({'error': 'Kérjük, először töltse ki a profil adatait!'}), 400

            data = request.get_json()
            components = data.get('components', [])
            special_requests = data.get('requests', '')

            # Email tartalom összeállítása
            email_content = "Új PC konfiguráció érkezett!\n\n"
            
            # Felhasználói adatok
            email_content += f"Megrendelő adatai:\n"
            email_content += f"Név: {user.profile.full_name}\n"
            email_content += f"Email: {user.email}\n"
            email_content += f"Telefonszám: {user.profile.phone}\n"
            email_content += f"Szállítási cím: {user.profile.address}\n\n"
            
            # Komponensek listája
            email_content += "Kiválasztott komponensek:\n"
            total_price = 0
            for component in components:
                email_content += f"- {component['category']}: {component['name']} ({component['price']} Ft)\n"
                total_price += int(component['price'])
            
            email_content += f"\nÖsszesen: {total_price} Ft"
            
            if special_requests:
                email_content += f"\n\nEgyéb kérések:\n{special_requests}"

            # Email küldése az admin és a felhasználó címére is
            msg = Message(
                'PC Konfiguráció Rendelés',
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_USERNAME'], user.email],  # Admin és felhasználó email címe
                reply_to=user.email  # Válasz a felhasználó címére menjen
            )
            msg.body = email_content
            mail.send(msg)

            return jsonify({'message': 'Konfiguráció sikeresen elküldve!'}), 200
        except Exception as e:
            print(f"Hiba az email küldése során: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/configurator')
    def configurator():
        return render_template('configurator.html')

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        try:
            user = User.query.get(session['user_id'])
            if not user:
                flash('Felhasználó nem található!', 'danger')
                return redirect(url_for('login'))

            if request.method == 'POST':
                # Form adatok ellenőrzése
                full_name = request.form.get('full_name')
                address = request.form.get('address')
                phone = request.form.get('phone')

                # Validáció
                if not full_name or not address or not phone:
                    flash("Minden mező kitöltése kötelező!", 'danger')
                    return redirect(url_for('profile'))

                try:
                    # Profil lekérése vagy létrehozása
                    user_profile = UserProfile.query.filter_by(user_id=user.id).first()
                    if not user_profile:
                        user_profile = UserProfile(user_id=user.id)
                        db.session.add(user_profile)
                    
                    # Profil adatok frissítése
                    user_profile.full_name = full_name
                    user_profile.address = address
                    user_profile.phone = phone
                    
                    # Profilkép kezelése
                    if 'profile_image' in request.files:
                        file = request.files['profile_image']
                        if file and file.filename:
                            try:
                                # Régi kép törlése
                                if user_profile.profile_image:
                                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], user_profile.profile_image)
                                    if os.path.exists(old_image_path):
                                        os.remove(old_image_path)
                                
                                # Új kép mentése
                                filename = secure_filename(file.filename)
                                new_filename = f"profile_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                                
                                app.logger.info(f"Saving file to: {file_path}")
                                file.save(file_path)
                                
                                if os.path.exists(file_path):
                                    app.logger.info(f"File saved successfully. Size: {os.path.getsize(file_path)} bytes")
                                    user_profile.profile_image = new_filename
                                else:
                                    app.logger.error("File save failed - file not found after save")
                                    raise Exception("File save failed")
                                    
                            except Exception as e:
                                app.logger.error(f"Error in file handling: {str(e)}")
                                if 'file_path' in locals() and os.path.exists(file_path):
                                    os.remove(file_path)
                                raise

                    db.session.commit()
                    flash('Profil sikeresen frissítve!', 'success')
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error updating profile: {str(e)}")
                    flash('Hiba történt a profil mentése során!', 'danger')
                
                return redirect(url_for('profile'))

            # GET kérés esetén
            return render_template('profile.html', user=user)

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error loading profile: {str(e)}")
            flash('Hiba történt a profil betöltése során!', 'danger')
            return redirect(url_for('dashboard'))

    @app.route('/view_configuration/<int:config_id>')
    @login_required
    def view_configuration(config_id):
        config = Configuration.query.get_or_404(config_id)
        if config.user_id != session['user_id']:
            flash('Nincs jogosultságod ehhez a konfigurációhoz!', 'danger')
            return redirect(url_for('profile'))
        return render_template('view_configuration.html', config=config)

    @app.route('/create_configuration', methods=['POST'])
    @login_required
    def create_configuration():
        try:
            name = request.form.get('name')
            
            # Komponensek összegyűjtése
            components = {
                'processor': request.form.get('processor'),
                'motherboard': request.form.get('motherboard'),
                'gpu': request.form.get('gpu'),
                'ram': request.form.get('ram'),
                'psu': request.form.get('psu'),
                'case': request.form.get('case'),
                'storage': request.form.get('storage'),
                'cooling': request.form.get('cooling')
            }
            
            # Üres értékek eltávolítása
            components = {k: v for k, v in components.items() if v}
            
            new_config = Configuration(
                user_id=session['user_id'],
                name=name,
                components=components
            )
            
            db.session.add(new_config)
            db.session.flush()
            
            # Új session-ben lekérjük a felhasználót és a konfigurációkat
            user = db.session.query(User).get(session['user_id'])
            db.session.refresh(user)
            
            # HTML generálása a friss konfigurációkhoz
            configs_html = ""
            for config in user.configurations:
                config_html = f'''
                <div class="config-item mb-4 p-3" style="background-color: #333; border-radius: 5px;">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="mb-0">{config.name}</h5>
                        <form method="POST" action="/delete_configuration/{config.id}" class="delete-form">
                            <button type="submit" class="btn btn-danger btn-sm">Törlés</button>
                        </form>
                    </div>
                '''
                if config.components:
                    if config.components.get('processor'):
                        config_html += f'<div>Processzor: {config.components["processor"]}</div>'
                    if config.components.get('motherboard'):
                        config_html += f'<div>Alaplap: {config.components["motherboard"]}</div>'
                    if config.components.get('gpu'):
                        config_html += f'<div>Videókártya: {config.components["gpu"]}</div>'
                    if config.components.get('ram'):
                        config_html += f'<div>RAM: {config.components["ram"]}</div>'
                    if config.components.get('psu'):
                        config_html += f'<div>Tápegység: {config.components["psu"]}</div>'
                    if config.components.get('case'):
                        config_html += f'<div>Gépház: {config.components["case"]}</div>'
                    if config.components.get('storage'):
                        config_html += f'<div>Tárhely: {config.components["storage"]}</div>'
                    if config.components.get('cooling'):
                        config_html += f'<div>Hűtés: {config.components["cooling"]}</div>'
                config_html += '</div>'
                configs_html += config_html
            
            # Véglegesítjük a tranzakciót
            db.session.commit()
            
            return jsonify({
                'success': True,
                'configs_html': configs_html
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/delete_configuration/<int:config_id>', methods=['POST'])
    @login_required
    def delete_configuration(config_id):
        try:
            # Új session-ben keressük meg a konfigurációt
            config = db.session.query(Configuration).get(config_id)
            if not config:
                return jsonify({'success': False, 'message': 'A konfiguráció nem található!'})
            
            if config.user_id != session['user_id']:
                return jsonify({'success': False, 'message': 'Nincs jogosultságod törölni ezt a konfigurációt!'})
            
            # Törlés és commit
            db.session.delete(config)
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

    @app.route("/")
    def home():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            try:
                # Ellenőrzés: üres mezők
                if not username or not email or not password:
                    flash('Minden mező kitöltése kötelező!', 'danger')
                    return redirect(url_for('register'))

                # Ellenőrzés: email vagy felhasználónév létezik-e
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    flash('Ez az email cím már regisztrálva van!', 'danger')
                    return redirect(url_for('register'))

                existing_username = User.query.filter_by(username=username).first()
                if existing_username:
                    flash('Ez a felhasználónév már foglalt!', 'danger')
                    return redirect(url_for('register'))

                # Új felhasználó létrehozása
                password_hash = generate_password_hash(password)
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash
                )
                db.session.add(new_user)
                db.session.commit()

                flash('Sikeres regisztráció! Most már bejelentkezhetsz.', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Registration error: {str(e)}")
                flash('Hiba történt a regisztráció során!', 'danger')
                return redirect(url_for('register'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            credential = request.form.get('credential')
            password = request.form.get('password')
            remember = request.form.get('remember')

            try:
                if not credential or not password:
                    flash('Kérjük, töltsd ki mindkét mezőt!', 'danger')
                    return redirect(url_for('login'))

                # Felhasználó keresése email vagy felhasználónév alapján
                user = User.query.filter(
                    (User.email == credential) | (User.username == credential)
                ).first()

                if user and check_password_hash(user.password_hash, password):
                    session['user_id'] = user.id
                    if remember:
                        session.permanent = True
                    flash('Sikeres bejelentkezés!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Hibás felhasználónév/email vagy jelszó!', 'danger')
                    return redirect(url_for('login'))

            except Exception as e:
                app.logger.error(f"Login error: {str(e)}")
                flash('Hiba történt a bejelentkezés során!', 'danger')
                return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            user = User.query.get(session.get('user_id'))
            if user:
                return render_template('dashboard.html', user=user)
            flash('Felhasználó nem található!', 'danger')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Dashboard error: {str(e)}")
            db.session.rollback()
            flash('Hiba történt az adatok betöltése során!', 'danger')
            return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Sikeresen kijelentkeztél!', 'success')
        return redirect(url_for('login'))

    # Fórum routes
    @app.route('/forum')
    def forum_home():
        try:
            # Először próbáljuk meg rollback-elni az esetleges függő tranzakciót
            db.session.rollback()
            
            # Majd próbáljuk lekérni a kategóriákat
            categories = ForumCategory.query.order_by(ForumCategory.order).all()
            return render_template('forum/home.html', categories=categories)
        except Exception as e:
            app.logger.error(f"Error in forum_home: {str(e)}")
            try:
                # Ha hiba van, tisztítsuk meg teljesen a kapcsolatot
                db.session.remove()
                db.engine.dispose()
                
                # Új session kezdése
                db.session.begin()
                
                # Újra próbáljuk lekérni a kategóriákat
                categories = ForumCategory.query.order_by(ForumCategory.order).all()
                return render_template('forum/home.html', categories=categories)
            except Exception as e:
                app.logger.error(f"Second attempt failed in forum_home: {str(e)}")
                flash('Hiba történt az adatok betöltése során. Kérlek, próbáld újra!', 'danger')
                return redirect(url_for('login'))

    @app.route('/forum/category/<int:category_id>')
    def forum_category(category_id):
        try:
            page = request.args.get('page', 1, type=int)
            
            # Kategória lekérése
            category = ForumCategory.query.get_or_404(category_id)
            
            # Témák lekérése eager loading-gal
            topics = db.session.query(ForumTopic)\
                .options(db.joinedload(ForumTopic.author))\
                .filter(ForumTopic.category_id == category_id)\
                .order_by(ForumTopic.is_pinned.desc(), ForumTopic.updated_at.desc())\
                .paginate(page=page, per_page=20)
            
            # Session frissítése
            db.session.expire_all()
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                topics_html = render_template('forum/_topics_list.html', 
                                           topics=topics,
                                           category=category)
                return jsonify({
                    'success': True,
                    'topics_html': topics_html
                })
            
            return render_template('forum/category.html', 
                                 category=category,
                                 topics=topics)
                                 
        except Exception as e:
            app.logger.error(f'Error in forum_category: {str(e)}')
            app.logger.exception("Részletes hiba:")  # Ez kiírja a teljes stack trace-t
            db.session.rollback()
            if app.debug:  # Csak debug módban mutatjuk a részletes hibát
                flash(f'Hiba történt a kategória betöltése során: {str(e)}', 'danger')
            else:
                flash('Hiba történt a kategória betöltése során!', 'danger')
            return redirect(url_for('forum_home'))

    @app.route('/forum/category/<int:category_id>/new', methods=['GET', 'POST'])
    @login_required
    def new_topic(category_id):
        try:
            category = ForumCategory.query.get_or_404(category_id)
            
            if request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')
                
                if not title or not content:
                    flash('Kérlek töltsd ki az összes mezőt!', 'danger')
                    return redirect(request.url)
                
                try:
                    topic = ForumTopic(
                        title=title,
                        content=content,
                        user_id=session['user_id'],
                        category_id=category_id
                    )
                    db.session.add(topic)
                    db.session.flush()
                    db.session.commit()
                    db.session.refresh(topic)  # Frissítjük az objektumot
                    
                    flash('A téma sikeresen létrehozva!', 'success')
                    return redirect(url_for('forum_topic', topic_id=topic.id))
                except Exception as e:
                    db.session.rollback()
                    flash('Hiba történt a téma mentése során!', 'danger')
                    return redirect(request.url)
            
            return render_template('forum/new_topic.html', category=category)
        except Exception as e:
            flash('Hiba történt!', 'danger')
            return redirect(url_for('forum_home'))

    @app.route('/forum/topic/<int:topic_id>')
    def forum_topic(topic_id):
        try:
            page = request.args.get('page', 1, type=int)
            
            # Téma lekérése eager loading-gal
            topic = db.session.query(ForumTopic)\
                .options(
                    db.joinedload(ForumTopic.author)
                    .joinedload(User.profile)
                )\
                .options(
                    db.joinedload(ForumTopic.category)
                )\
                .filter_by(id=topic_id)\
                .first_or_404()
            
            # Válaszok lekérése eager loading-gal
            replies = db.session.query(ForumReply)\
                .options(
                    db.joinedload(ForumReply.author)
                    .joinedload(User.profile)
                )\
                .options(
                    db.joinedload(ForumReply.upvotes)
                )\
                .filter_by(topic_id=topic_id)\
                .order_by(ForumReply.created_at.asc())\
                .paginate(page=page, per_page=10)
            
            # Nézettség növelése
            if not request.headers.get('X-Requested-With'):  # Csak ha nem AJAX kérés
                topic.view_count += 1
                db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                replies_html = render_template('forum/_replies_list.html',
                                            replies=replies,
                                            topic=topic)
                return jsonify({
                    'success': True,
                    'replies_html': replies_html
                })
            
            return render_template('forum/topic.html',
                                 topic=topic,
                                 replies=replies)
                             
        except Exception as e:
            app.logger.error(f'Error in forum_topic: {str(e)}')
            app.logger.exception("Részletes hiba:")
            db.session.rollback()
            flash('Hiba történt a téma betöltése során!', 'danger')
            return redirect(url_for('forum_home'))

    @app.route('/forum/topic/<int:topic_id>/reply', methods=['POST'])
    @login_required
    def reply_to_topic(topic_id):
        try:
            content = request.form.get('content')
            if not content:
                return jsonify({'success': False, 'message': 'A válasz tartalma nem lehet üres!'})

            # Téma lekérése eager loading-gal
            topic = db.session.query(ForumTopic)\
                .options(
                    db.joinedload(ForumTopic.replies)
                    .joinedload(ForumReply.author)
                    .joinedload(User.profile)
                )\
                .filter_by(id=topic_id)\
                .first_or_404()

            # Új válasz létrehozása
            reply = ForumReply(
                content=content,
                user_id=session['user_id'],
                topic_id=topic_id
            )
        
            db.session.add(reply)
            db.session.flush()
            db.session.refresh(reply)
        
            # Lekérjük az összes választ újra eager loading-gal
            page = request.args.get('page', 1, type=int)
            replies = db.session.query(ForumReply)\
                .options(
                    db.joinedload(ForumReply.author)
                    .joinedload(User.profile)
                )\
                .options(
                    db.joinedload(ForumReply.upvotes)
                )\
                .filter_by(topic_id=topic_id)\
                .order_by(ForumReply.created_at.desc())\
                .paginate(page=page, per_page=10)
        
            # Explicit commit
            db.session.commit()
        
            # Rendereljük a válaszok listáját
            replies_html = render_template('forum/_replies_list.html',
                                         replies=replies,
                                         topic=topic)
        
            return jsonify({
                'success': True,
                'message': 'Válasz sikeresen elküldve!',
                'replies_html': replies_html
            })
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error in reply_to_topic: {str(e)}')
            app.logger.exception("Részletes hiba:")
            return jsonify({
                'success': False,
                'message': 'Hiba történt a válasz mentése során!'
            })

    @app.route('/forum/reply/<int:reply_id>/upvote', methods=['POST'])
    @login_required
    def upvote_reply(reply_id):
        try:
            app.logger.info(f"Upvote request for reply_id: {reply_id}")  # Debug log
        
            # Először ellenőrizzük, hogy létezik-e a válasz
            reply = ForumReply.query.get(reply_id)
            if not reply:
                app.logger.error(f"Reply not found with id: {reply_id}")  # Debug log
                return jsonify({
                    'success': False,
                    'message': 'A válasz nem található!'
                }), 404
            
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'Nincs bejelentkezett felhasználó!'
                })
            
            app.logger.info(f"Processing upvote for reply_id: {reply_id}, user_id: {user_id}")  # Debug log
            
            # Ellenőrizzük, hogy van-e már upvote ettől a felhasználótól
            existing_upvote = ForumUpvote.query.filter_by(
                user_id=user_id,
                reply_id=reply_id
            ).first()
        
            if existing_upvote:
                # Ha már van upvote, akkor töröljük
                app.logger.info(f"Removing existing upvote for reply_id: {reply_id}")  # Debug log
                db.session.delete(existing_upvote)
                message = 'Upvote visszavonva!'
                has_upvoted = False
            else:
                # Ha még nincs, akkor létrehozunk egyet
                app.logger.info(f"Creating new upvote for reply_id: {reply_id}")  # Debug log
                upvote = ForumUpvote(
                    user_id=user_id,
                    reply_id=reply_id
                )
                db.session.add(upvote)
                message = 'Upvote sikeresen hozzáadva!'
                has_upvoted = True
        
            try:
                db.session.commit()
                app.logger.info(f"Successfully committed upvote changes for reply_id: {reply_id}")  # Debug log
            except Exception as e:
                app.logger.error(f"Error committing upvote changes: {str(e)}")  # Debug log
                db.session.rollback()
                raise
            
            # Frissítjük a válasz upvote számát
            upvotes_count = db.session.query(ForumUpvote).filter_by(reply_id=reply_id).count()
            app.logger.info(f"Current upvote count for reply_id {reply_id}: {upvotes_count}")  # Debug log
        
            return jsonify({
                'success': True,
                'message': message,
                'upvotes': upvotes_count,
                'has_upvoted': has_upvoted
            })
        
        except Exception as e:
            app.logger.error(f'Error in upvote_reply: {str(e)}')
            app.logger.exception("Részletes hiba:")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Hiba történt az upvote során!'
            })

    @app.route('/forum/search')
    def forum_search():
        query = request.args.get('q', '')
        if not query:
            return redirect(url_for('forum_home'))
        
        page = request.args.get('page', 1, type=int)
        topics = ForumTopic.query.filter(
            db.or_(
                ForumTopic.title.ilike(f'%{query}%'),
                ForumTopic.content.ilike(f'%{query}%')
            )
        ).order_by(ForumTopic.created_at.desc())\
         .paginate(page=page, per_page=20)
        
        return render_template('forum/search.html', topics=topics, query=query)

    @app.route('/service')
    def service():
        return render_template('service.html')

    @app.route('/diagnostics')
    def diagnostics():
        return render_template('diagnostics.html')