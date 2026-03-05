import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Upload configuration
UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size


class Config(object):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SECRET_KEY = "UBERS3Cr3tKeyBr0"
    JWT_SECRET_KEY = "Kj31dsh4sF0uNDH1STE4SP0ON!"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'Application.db')}"
    FLASK_ADMIN_SWATCH = "cerulean"
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH


class DevelopmentConfig(Config):
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False


APP_CONFIG = {"development": DevelopmentConfig, "production": ProductionConfig}
