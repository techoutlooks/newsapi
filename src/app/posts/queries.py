from collections import defaultdict
from itertools import chain

from ariadne import ObjectType, convert_kwargs_to_snake_case
from bson import ObjectId
from bson.errors import InvalidId
from daily_query.mongo import Collection

from app.database import engine
from app.posts.constants import \
    POST_SIBLINGS_FIELD, POST_RELATED_FIELD, POST_PREVIOUS_FIELD, POST_NEXT_FIELD, \
    POST_ACTIONS

from app.posts.utils import get_post_stats_for_action, format_post

query = ObjectType("Query")


@query.field("stats")
@convert_kwargs_to_snake_case
def resolve_stats(*_, from_date=None, to_date=None, first=None, recursive=False):
    """
    Compile stats for posts matching given date range and count.
    :returns dict: stats by action for all matched posts.
    """

    posts = list(engine.search(
        from_date=from_date, to_date=to_date,
        flatten=True, first=first
    ))

    stats = defaultdict(list)
    for key in POST_ACTIONS:
        action_stats = list(filter(None, map(
            lambda p: get_post_stats_for_action(format_post(p), key, recursive=recursive),
            posts
        )))
        action_stats = list(chain.from_iterable(action_stats))
        stats[key] += action_stats

    return stats


@query.field("post")
@convert_kwargs_to_snake_case
def resolve_post(*_, post_id=None, adjacent_docs_included=1):
    """
    Find the given post across across all collections (days).
    Embeds #adjacent_posts previous/next posts.
    :param adjacent_docs_included: number of previous/next posts to insert
    :param post_id:
    :return:
    """

    # exclude ObjectId(None) which generates a random ObjectId
    if not post_id:
        return

    # ensure the `post_id` is valid ObjectId
    try:
        object_id = ObjectId(post_id)
    except InvalidId:
        return

    opts = {"filter": {"_id": object_id}, "first": 1,
            "adjacent_docs_included": adjacent_docs_included}
    posts = list(search_posts(**opts, flatten=True))
    if not len(posts):
        return

    return posts[0]


@query.field("posts")
@convert_kwargs_to_snake_case
def resolve_posts(*_, type=None, post_ids=None, **kwargs):
    """
    List of posts across all collections matching given criteria.
    """
    post_filter = {}
    if type:
        post_filter.update({'type': {'$eq': type}})

    if post_ids:
        post_filter.update({'_id': {'$in': [ObjectId(x) for x in post_ids]}})

    posts = list(search_posts(flatten=True, filter=post_filter, **kwargs))
    return posts


@query.field("tags")
@convert_kwargs_to_snake_case
def resolve_tags(*_, **kwargs):
    items = engine.find(**kwargs)
    return chain.from_iterable(
        [cursor.distinct('tags') for cursor, col in items]
    )


@query.field("tagCounts")
@convert_kwargs_to_snake_case
def resolve_by_tags(*_, days=None, days_from=None, days_to=None):
    """
    Ordered mapping of post counts for each tag
    in the input date range.
    Eg.
        [{'postCount': 2, 'tag': 'Carburants'}, {'postCount': 1, 'tag': 'Dubréka'}]
        {'postCount': 1, 'tag': 'Déguerpissement'}, ...]
    """

    pipelines = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "postCount": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "tag": "$_id", "postCount": 1}}
    ]

    counts = chain.from_iterable([
        collection.aggregate(pipelines)
        for collection in engine.get_collections(
            days=days, days_from=days_from, days_to=days_to)
    ])

    return counts


def search_posts(
        days=None, days_from=None, days_to=None,
        first=None, filter=None, fields=None, exclude=None,
        adjacent_docs_included=None, flatten=False,
):
    """
    Walk posts across all collections (days) in date range,
    applying following patches for every post:

    - insert similar (sibling and related) posts under keys
      POST_SIBLINGS_FIELD, POST_RELATED_FIELD resp.
    - insert adjacent (previous and next) posts under keys:
      POST_PREVIOUS_FIELD and POST_NEXT_FIELD resp.
    - convert `_id` of type `ObjectId` into `id` of type `str` everywhere.

    Nota: search for similar and adjacent posts only in same collection
        as the referred to post: nlp tasks marks similar posts for any
        given day only.

        since posts are

    :param flatten: whether to also return the collection with the post, as a tuple
        ie., returns [Post, ...]? or [(Post,Collection), ...]?
    :param adjacent_docs_included: # of previous/next posts to also embed with every post.
        `utils.find()` for other params.

    #TODO: better handling for POST_SIBLINGS_FIELD not found error??
    (newsbot's `nlpsimilarity` must be run first, prior to `newsapi` safely serving posts )
    """

    def _expand_similar(data, col: Collection):
        """ Expand list [{"_id": <ObjectId>, ..}, ...] of similar posts into full post.
        **_id** of similar post from same collection as the referred to post.
        """
        similar_posts = list(col.find({
            "_id": {"$in": list(map(lambda x: x["_id"], data))}}
        ))

        return list(map(format_post, similar_posts))

    items = list(engine.search(days=days, days_from=days_from, days_to=days_to,
                               first=first, filter=filter, fields=fields, exclude=exclude))

    for post, col in items:

        # patch every post's *siblings* and *related* fields
        # with full, expanded post data. original db data looks like:
        # { "siblings": [{"_id": <doc_id>, "score": <similarity_score>}, ...]}
        # { "related": [{"_id": <doc_id>, "score": <similarity_score>}, ...]}
        for f in (POST_SIBLINGS_FIELD, POST_RELATED_FIELD):
            try:
                post[f] = _expand_similar(post[f], col)
            except KeyError:
                post[f] = []

        # patch every post with `adjacent_docs_included` adjacent posts in collection,
        # ie., `adjacent_docs_included` posts before and after the current post.
        # { "siblings": [{"_id": <doc-id>, "score": <similarity-score>}, ...]}
        # TODO: add option not to load all fields on adjacent posts.
        if adjacent_docs_included:
            previous_posts = list(
                col.find({'_id': {'$lt': post["_id"]}}).sort([('_id', -1)])
                    .limit(adjacent_docs_included)
            )
            post[POST_PREVIOUS_FIELD] = list(map(format_post, previous_posts))

            next_posts = list(
                col.find({'_id': {'$gt': post["_id"]}})
                    .sort('_id').limit(adjacent_docs_included)
            )
            post[POST_NEXT_FIELD] = list(map(format_post, next_posts))

        post = format_post(post)
        yield (col, post) \
            if not flatten else post
