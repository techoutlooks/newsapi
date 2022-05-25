"""
https://flask.palletsprojects.com/en/2.0.x/tutorial/factory/
https://luciano.defalcoalfano.it/blog/show/how_create_minimal_flask_project_5th_part
"""
import logging
import os
from logging.handlers import RotatingFileHandler

import flask

from app import config
from app.config import get_config


def create_app(config_class="app.config.DevConfig"):
    """
    Create and configure an instance of the Flask application.
    export FLASK_APP=app
    FLASK_ENV=development
    flask run
    """

    app = flask.Flask(__name__, instance_relative_config=True)
    # ensure the instance folder exists
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # CONFIG
    # ======
    set_config(app, config_class)
    set_logger(app)

    # CORS
    # ====
    from flask_cors import CORS
    CORS(app)

    # BLUEPRINTS
    # ==========
    # from posts import posts
    # app.register_blueprint(posts, url_prefix='posts/')

    print(app.url_map)
    return app


def set_config(app, env=None):
    app.config.from_mapping({

        # builtin
        "DEBUG": True,
        "SECRET_KEY": "dev",
        # "SERVER_NAME": "0.0.0.0:5000",

        # custom
        "LOG": {
            "DIR": os.path.join(app.instance_path, 'logs'),
            "FILE": os.path.join(app.instance_path, 'logs/arise-news.log'),
            "BUFSIZE": 102400,
            "FILE_HANDLER_LEVEL": logging.DEBUG,
            "APP_LOGGER_LEVEL": logging.DEBUG,
        },

    })

    app.config.from_object(get_config(env))
    app.config.from_pyfile('app.cfg', silent=True)

    # with app.app_context():
    #     from .database import db
    #     db.init_app(app)
    #     migrate.init_app(app, db)

    with app.app_context():
        from . import database
        from . import routes


def set_logger(app):
    if not os.path.exists(app.config['LOG']['DIR']):
        os.mkdir(app.config['LOG']['DIR'])

    file_handler = RotatingFileHandler(
        app.config['LOG']['FILE'],
        maxBytes=app.config['LOG']['BUFSIZE'], backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(app.config['LOG']['FILE_HANDLER_LEVEL'])
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config['LOG']['APP_LOGGER_LEVEL'])
    app.logger.debug('arise-news app starts ...')
