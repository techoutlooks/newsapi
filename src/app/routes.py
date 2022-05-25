import flask
from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, gql, load_schema
from ariadne.constants import PLAYGROUND_HTML
from flask import Blueprint

# from app import app
from app.posts.queries import query
from app.posts.mutation import mutation


graphql = Blueprint("graphql", __name__)


type_defs = gql(load_schema_from_path("src/app/schema.graphql"))
schema = make_executable_schema(type_defs, query, mutation)


@flask.current_app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@flask.current_app.route("/graphql", methods=["POST"])
def graphql_server():

    # GraphQL queries are always sent as POST
    data = flask.request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value=flask.request,
        debug=flask.current_app.debug
    )

    status_code = 200 if success else 400
    return flask.jsonify(result), status_code
