import os

class Config:
    # Alap konfiguráció
    SECRET_KEY = 'dqYlV9C2I1cBuey'
    
    # MySQL konfiguráció
    MYSQL_HOST = 'itspcman.mysql.pythonanywhere-services.com'
    MYSQL_USER = 'itspcman'  
    MYSQL_PASSWORD = 'dqYlV9C2I1cBuey'  
    MYSQL_DB = 'itspcman$pcman'
    
    # SQLAlchemy konfiguráció
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 280,  
        'pool_pre_ping': True,
    }
    
    # Feltöltési konfiguráció
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max-size
