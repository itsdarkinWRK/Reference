from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Component, UserProfile, Configuration
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from sqlalchemy import text
from functools import wraps
import os
from werkzeug.utils import secure_filename
import time
from datetime import datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Kérjük, jelentkezz be a folytatáshoz!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'itsdarkinwrk@gmail.com'
    # Az App Password-öt kell használni, amit a Google Fiók beállításokban lehet generálni
    app.config['MAIL_PASSWORD'] = 'huta umpa nmgl ajym'
    mail = Mail(app)

    # Statikus mappák beállítása
    static_dir = os.path.join(app.root_path, 'static')
    uploads_dir = os.path.join(static_dir, 'uploads')
    
    # Létrehozzuk a mappákat, ha nem léteznek
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)

    # Profilkép elérési útvonal ellenőrzése
    def get_profile_image_path(filename):
        if not filename:
            return None
        return os.path.join(uploads_dir, filename)

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
        components = [dict(row) for row in result]
        return jsonify(components)

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

    def init_uploads():
        """Inicializálja a feltöltési mappákat"""
        # Alap útvonalak
        base_path = os.path.abspath(os.path.dirname(__file__))
        local_uploads = os.path.join(base_path, 'static', 'uploads')
        pythonanywhere_uploads = '/home/itspcman/pcman/static/uploads'
        
        # Ellenőrizzük és létrehozzuk a megfelelő mappát
        uploads_dir = pythonanywhere_uploads if os.path.exists('/home/itspcman') else local_uploads
        os.makedirs(uploads_dir, exist_ok=True)
        
        print(f"Upload directory initialized: {uploads_dir}")
        return uploads_dir

    UPLOADS_DIR = init_uploads()

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            try:
                # Új session-ben kérjük le a profilt
                profile = db.session.query(UserProfile).filter_by(user_id=session['user_id']).first()
                if not profile:
                    profile = UserProfile(user_id=session['user_id'])
                    db.session.add(profile)
                    db.session.commit()  # Azonnal commitoljuk az új profilt
                    # Új session-ben kérjük le újra
                    profile = db.session.query(UserProfile).filter_by(user_id=session['user_id']).first()
                
                # Alapadatok mentése
                profile.full_name = request.form.get('full_name')
                profile.address = request.form.get('address')
                profile.phone = request.form.get('phone')
                
                # Profilkép kezelése
                if 'profile_image' in request.files:
                    file = request.files['profile_image']
                    if file and file.filename:
                        try:
                            # Régi kép törlése
                            if profile.profile_image:
                                old_image_path = os.path.join(UPLOADS_DIR, profile.profile_image)
                                if os.path.exists(old_image_path):
                                    os.remove(old_image_path)
                                    print(f"Deleted old image: {old_image_path}")
                            
                            # Új kép mentése
                            filename = secure_filename(file.filename)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            new_filename = f"profile_{session['user_id']}_{timestamp}_{filename}"
                            file_path = os.path.join(UPLOADS_DIR, new_filename)
                            
                            print(f"Saving file to: {file_path}")
                            file.save(file_path)
                            
                            if os.path.exists(file_path):
                                print(f"File saved successfully. Size: {os.path.getsize(file_path)} bytes")
                                
                                # Új tranzakcióban mentjük a profile_image értéket
                                db.session.begin_nested()
                                try:
                                    profile.profile_image = new_filename
                                    db.session.commit()
                                    print(f"Profile image name saved to database: {new_filename}")
                                except Exception as db_error:
                                    print(f"Error saving to database: {str(db_error)}")
                                    db.session.rollback()
                                    os.remove(file_path)  # Töröljük a fájlt, ha nem sikerült menteni
                                    raise
                            else:
                                raise Exception("File save failed - file not found after save")
                                
                        except Exception as e:
                            print(f"Error in file handling: {str(e)}")
                            if 'file_path' in locals() and os.path.exists(file_path):
                                os.remove(file_path)
                            raise
            
                # Végleges mentés
                try:
                    db.session.commit()
                    print(f"Final commit successful")
                    
                    # Ellenőrzés új session-ben
                    with db.session.begin():
                        check_profile = db.session.query(UserProfile).get(profile.id)
                        print(f"Profile verification - ID: {check_profile.id}, Image: {check_profile.profile_image}")
                    
                    flash('Profil sikeresen frissítve!', 'success')
                except Exception as commit_error:
                    print(f"Error during final commit: {str(commit_error)}")
                    db.session.rollback()
                    raise
            
            except Exception as e:
                print(f"Profile update error: {str(e)}")
                flash('Hiba történt a profil mentése során!', 'danger')
        
            return redirect(url_for('profile'))
        
        # GET kérés esetén
        try:
            with db.session.begin():
                user = db.session.query(User).get(session['user_id'])
                if user and user.profile:
                    print(f"Current profile - ID: {user.profile.id}, Image: {user.profile.profile_image}")
                    
                    if user.profile.profile_image:
                        image_path = os.path.join(UPLOADS_DIR, user.profile.profile_image)
                        print(f"Checking profile image: {image_path}")
                        exists = os.path.exists(image_path)
                        print(f"Image exists: {exists}")
                        
                        if not exists:
                            print("Image not found, resetting profile_image")
                            user.profile.profile_image = None
                            db.session.commit()
        
            return render_template('profile.html', user=user)
            
        except Exception as e:
            print(f"Error loading profile: {str(e)}")
            flash('Hiba történt a profil betöltése során!', 'danger')
            return redirect(url_for('home'))

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
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            password_hash = generate_password_hash(password)

            # Ellenőrzés: Felhasznál ónév vagy email létezik-e
            existing_user = User.query.filter(
                (User .username == username) | (User .email == email)
            ).first()
            if existing_user:
                flash('A felhasználónév vagy email már létezik!', 'danger')
                return redirect(url_for('register'))

            # Új felhasználó hozzáadása az adatbázishoz
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()

            flash('Regisztráció sikeres!', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                credential = request.form.get('credential')
                password = request.form.get('password')

                user = User.query.filter(
                    (User.username == credential) | (User.email == credential)
                ).first()

                if user and check_password_hash(user.password_hash, password):
                    session['user_id'] = user.id
                    db.session.commit()
                    flash('Sikeres bejelentkezés!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Érvénytelen felhasználónév/email vagy jelszó!', 'danger')
            except Exception as e:
                db.session.rollback()
                flash('Hiba történt a bejelentkezés során. Kérjük próbálja újra.', 'danger')
                return render_template('login.html')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Sikeresen kijelentkeztél!', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        return render_template('dashboard.html', user=user)

    @app.route('/questions', methods=['GET', 'POST'])
    def questions():
        if request.method == 'POST':
            # Itt kezelheted a kérdéseket, ha van ilyen logika
            pass
        return render_template('questions.html')