from app.utils import get_env_variable


MONGO_URI = get_env_variable('MONGO_URI')


class Config(object):
    DEBUG = False
    TESTING = False

    # SQLAlchemy
    MONGO_URI = MONGO_URI

    # Silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API settings
    API_PAGINATION_PER_PAGE = 10


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True


class ProdConfig(Config):
    # production config
    pass


def get_config(env=None):
    if env is None:
        try:
            env = get_env_variable('ENV')
        except Exception:
            env = 'development'
            print('env is not set, using env:', env)

    if env == 'production':
        return ProdConfig()
    elif env == 'test':
        return TestConfig()

    return DevConfig()
