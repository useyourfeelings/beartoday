import os
basedir = os.path.abspath(os.path.dirname(__file__))

jquery_js_url = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js'
semantic_js_url = 'https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.7/semantic.min.js'
semantic_css_url = 'https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.7/semantic.css'
avatar_site = 'https://gravatar.com/avatar/'
gallery_dir = '/static/images/gallery/'
background_image = '/static/images/background/1811.png'

class Config:
    DEBUG = True
    MAIL_DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_ECHO = True
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = '123@gmail.com'
    MAIL_PASSWORD = '123'
    BT_MAIL_SUBJECT_PREFIX = '[BEAR.TODAY]'
    BT_MAIL_SENDER = '123<123@gmail.com>'
    BT_ADMIN = os.environ.get('BT_ADMIN')
    
    SESSION_COOKIE_NAME = "l321"

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'mysql+mysqlconnector://123:123@localhost/BEARTODAY'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'mysql+mysqlconnector://123:123@localhost/BEARTODAY'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+mysqlconnector://123:123@localhost/BEARTODAY'


config_list = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
