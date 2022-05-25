from tests.conftest import test_client


def test_resolve_posts(test_client):

    response = test_client.post("/graphql", json={"query": '{ posts {id title} }'})
    assert response.status_code == 200
    assert "data" in response.json
    assert "posts" in response.json["data"]
