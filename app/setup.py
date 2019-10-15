import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap

from app.database import setup_database
from app.routes import setup_routes

load_dotenv()

# Deployment environment, either "production" or "development"
app_env = os.environ['FLASK_ENV']

# Configuration for logging module
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s-%(name)s] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S%z'
        }
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            # 'stream': 'ext://sys.stdout',
            'formatter': 'default',
            'level': 'DEBUG' if app_env == 'production' else 'INFO'
        },
        'file_handler': {
            'class': 'logging.FileHandler',
            'filename': '.log',
            'formatter': 'default',
            'level': 'DEBUG'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['default'] if app_env == 'production' else ['default', 'file_handler']
    }
})


def create_app() -> Flask:
    new_app = Flask(__name__)

    # Load configuration settings
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

    new_app.logger.info('Application initialized.')
    return new_app
