import os.path

import flask
from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, gql, ObjectType
from ariadne.constants import PLAYGROUND_HTML
from flask import Blueprint


# ObjectType instances mapping to schema's Query and Mutation.
# will resolve dynamically, thanks to calling `load_schema()`
query = None
mutation = None

graphql = Blueprint("graphql", __name__)


def load_schema(path: str):
    """
    Loads the schema dynamically, avoiding circular imports.
    Reason? let the schema binding of type vs. resolvers be aware of
    the resolver's code while initializing the query/mutation ObjectType
    instances above. Read further in comments below.
    https://ariadnegraphql.org/docs/resolvers.html
    """

    # set as globals to resolve import of `query` and `mutation` binders
    # that are required by the modules imported next; namely the resolvers
    # imported by app.posts, app.ezines
    global query
    global mutation
    query = ObjectType("Query")
    mutation = ObjectType("Mutation")

    # binding resolvers to query/mutation types does not work properly if
    # the resolver's definition are not read while binding
    import app.posts
    import app.ezines
    type_defs = gql(load_schema_from_path(path))
    return make_executable_schema(type_defs, query, mutation)


schema = load_schema(f"{os.path.dirname(__file__)}/schema.graphql")


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
