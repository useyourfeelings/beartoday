from app.tool.tools import dbg
dbg("app.py")

from flask import Flask
from flask.ext.mail import Mail
#from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.babel import Babel

from .flasksui import *

flasksui = SUI()

mail = Mail()
#moment = Moment()
db = SQLAlchemy(session_options = {'autocommit':False})

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

import config as config

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config.config_list[config_name])
    config.config_list[config_name].init_app(app)

    flasksui.init_app(app)
    mail.init_app(app)
    #moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    babel = Babel(app, 'en')

    from .site import site_blueprint
    from .auth import auth_blueprint
    
    app.register_blueprint(site_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
