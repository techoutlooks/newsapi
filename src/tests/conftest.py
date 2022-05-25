import pytest

from app import create_app


@pytest.fixture(scope="module")
def app():

    # `yield`, so that execution is passed to the test functions.
    app = create_app({
        "TESTING": True     # so exceptions can propagate to test client
    })

    yield app


@pytest.fixture(scope="module")
def test_client(app):
    # return `FlaskClient` (subclasses `werkzeug.test.Client`) instance
    # simulate requests to a WSGI application without starting a server.
    # The client has methods for making different types of requests,
    # as well as managing cookies across requests
    return app.test_client()

    # with app.test_client as c:
    #     with app.app_context():
    #         yield c


# coverage run -m pytest -v && coverage report -m --omit="venv/*"
# pytest --cov=newsapi tests/

# coverage html --omit=tests/ -d tests/coverage
