import os


class BaseConfig():
    PROJECT = 'Chariots'
    DEBUG = False
    TESTING = False

    SECRET_KEY = os.environ['SECRET_KEY']

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(BaseConfig):
    LOG_DESTINATION_FILE = '.log'

    # Heroku PostgreSQL passes connection URL as env var
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class DevelopmentConfig(BaseConfig):
    DEBUG = True

    LOG_DESTINATION_FILE = '.log'
    # SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://echo:1231@localhost/chariots'
