from app.database import get_collections

# def test_resolve_posts(mocker):
#
#     response = test_client.post("/graphql", json={"query": '{ posts {id title} }'})
#     assert response.status_code == 200
#     assert "data" in response.json
#     assert "posts" in response.json["data"]


def test_get_collections_returns_empty_list_with_wrong_date_range(mocker, app, mongo, from_date, to_date):

    with app.app_context():
        pass

    collection_names = ['2021-06-21', '2021-07-06', '2021-05-31', '2021-06-10', '2021-06-09', '2021-06-22',
                        '2021-06-08', '2021-06-23', '2021-06-06', '2021-06-03', '2021-06-01', '2021-06-04',
                        '2021-07-01', '2021-06-12']
    mocker.patch('newsapi.posts.queries.db.list_collection_names', return_value=collection_names)
    collections = [mongo.db.collection[name] for name in collection_names]

    assert collections == get_collections(from_date, to_date)