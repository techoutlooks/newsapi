import flask

ezines = flask.Blueprint('ezines', __name__)


from . import sports
