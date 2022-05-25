from ariadne import ObjectType, convert_kwargs_to_snake_case
from bson import ObjectId

from app.posts.constants import POST_STATS_FIELD
from app.posts.queries import format_post
from app.posts.utils import parse_post_url
from app.database import get_db, engine

db = get_db()

mutation = ObjectType("Mutation")


@mutation.field("saveStats")
@convert_kwargs_to_snake_case
def resolve_save_stats(*_, stats=None):
    """
    Save post stats to the database.
    {'clicks': [{'on': {'name': 'posts/612acbbc20abcbba8e42fd04', 'value': '1983'}}]}
    """

    print("**** saveStats saving stats= ", stats)

    posts = []

    # save (overwrite) clicks statistics,
    # one matching post at a time
    # matches click url 'post/612acbbc20abcbba8e42fd04'
    # TODO: match id '612acbbc20abcbba8e42fd04' as well as url
    for click in stats['clicks']:
        url = click["on"]["name"]
        post_id = parse_post_url(url)["id"]
        if post_id:

            # low level `database.find()` faster than `db.search()`
            # TODO: factorise into `database.find_one()` cf. resolve_post()
            items = list(engine.find(first=1, filter={"_id": ObjectId(post_id)}))
            if not len(items):
                break

            # update post
            col_name, _ = items[0]
            col = get_existing_collection(col_name)
            post = col.find_one_and_update(
                {"_id": ObjectId(post_id)},
                {"$set": {POST_STATS_FIELD: stats}}
            )

            # result
            posts.append(format_post(post))

    # save other posts stats
    # ...

    return posts
