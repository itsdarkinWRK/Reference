from flask import Flask
from routes import register_routes
from flask_migrate import Migrate
from database import db


app = Flask(__name__)
app.secret_key = 'dqYlV9C2I1cBuey'

# Konfiguráció
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://itspcman:dqYlV9C2I1cBuey@itspcman.mysql.pythonanywhere-services.com/itspcman$pcman'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Maximális kapcsolatok száma a poolban
    'pool_recycle': 280,  # Kapcsolatok újrahasznosítása 280 másodpercenként
    'pool_pre_ping': True,  # Kapcsolat ellenőrzése minden használat előtt
    'pool_timeout': 30,  # Várakozási idő, ha nincs szabad kapcsolat
    'max_overflow': 5,  # Extra kapcsolatok száma, ha a pool tele van
}

# Adatbázis inicializálása
db.init_app(app)

# Flask-Migrate inicializálása
migrate = Migrate(app, db)

# Útvonalak regisztrálása
register_routes(app)

@app.before_request
def before_request():
    """Minden kérés előtt ellenőrizzük a kapcsolatot"""
    try:
        # Először próbáljuk meg rollback-elni az esetleges függő tranzakciót
        db.session.rollback()
        # Majd ellenőrizzük a kapcsolatot
        db.session.execute('SELECT 1')
    except Exception as e:
        # Ha hiba van, tisztítsuk meg teljesen a kapcsolatot
        db.session.remove()
        db.engine.dispose()
        # Új session kezdése
        db.session.begin()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Létrehozza az adatbázist és a táblákat
        app.run(debug=True)