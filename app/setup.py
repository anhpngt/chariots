import os

from dotenv import load_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap
from logging.handlers import RotatingFileHandler
import logging

from app.database import setup_database
from app.routes import setup_routes

load_dotenv()


def create_app() -> Flask:
    new_app = Flask(__name__)

    # Load configuration settings
    app_env = os.environ['ENVIRONMENT']
    if app_env == 'production':
        new_app.config.from_object('app.config.ProductionConfig')
    elif app_env == 'development':
        new_app.config.from_object('app.config.DevelopmentConfig')
    else:
        print('Unknown ENVIRONMENT variable, loading development configurations.')
        new_app.config.from_object('app.config.DevelopmentConfig')

    # Setup database
    setup_database(new_app)

    # Setup routes
    setup_routes(new_app)

    _ = Bootstrap(new_app)

    new_app.logger.info('App init successful')
    return new_app


def setup_logging(app: Flask) -> None:
    formatter = logging.Formatter(fmt='[{levelname}] {asctime} ({module}): {message}', style='{')
    handler = RotatingFileHandler(app.config['LOG_DESTINATION_FILE'], maxBytes=1073741824, backupCount=5)
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    if app.config['DEBUG']:
        app.logger.setLevel(logging.DEBUG)
