import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_principal import Principal, identity_loaded


# Initialize extensions without binding to app
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
principals = Principal()

def create_app(test_config=None):
    """
    Create and configure an instance of the Flask application.

    Args:
        test_config (dict): Configuration dictionary usually for testing.

    Returns:
        Flask: The configured Flask application instance
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping (
        SECRET_KEY = "dev",       # Should be changed in production!
        WTF_CSRF_ENABLED = False, # Should be changed in production!
        SQLALCHEMY_DATABASE_URI = "sqlite:///flask.db",
        TEMPLATES_AUTO_RELOAD = True, # FOR DEBUGGING PURPOSES
        # store database file flask.db in the instance folder
        DATABASE = os.path.join(app.instance_path, "flask.db"),
        UPLOAD_FOLDER = os.path.join(app.root_path, 'static','images'),
        ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    )

    # if a test_config is specified load it, otherwise load the instance config if it exists
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # bind the extensions to the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app) 
    principals.init_app(app)

    # configuring login_manager settings
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'

    # registering callback functions for login_manager and principal
    from . import auth
    login_manager.user_loader(auth.load_user_from_id)
    identity_loaded.connect_via(app)(auth.on_identity_loaded)

    # Registering the blueprints to the app
    app.register_blueprint(auth.bp)

    from . import logic
    app.register_blueprint(logic.bp)
    app.add_url_rule('/', endpoint='landing') # landing page is default route

    from . import images
    app.register_blueprint(images.bp)

    from . import model
    model.init_db(app)

    return app