from collections import defaultdict
from itertools import chain
from typing import Iterable, Literal, Callable, Tuple

import pytz as pytz
from ariadne import convert_kwargs_to_snake_case
from babel.core import Locale
from babel.numbers import get_territory_currencies
from bson import ObjectId
from bson.errors import InvalidId
from daily_query.base import Doc

from app.database import engine
from app.posts.constants import \
    POST_SIBLINGS_FIELD, POST_RELATED_FIELD, POST_PREVIOUS_FIELD, POST_NEXT_FIELD, \
    POST_TYPE_FIELD, POST_IS_META_FIELD, VALUE_FIELD, NAME_FIELD, \
    POST_ACTIONS, POST_FETCH_LIMIT, METAPOST
from app.posts.utils import get_post_stats_for_action
from app.routes import query
from app.utils import compose

from app.utils.agg import Aggregate as Agg


@query.field("mostPublished")
@convert_kwargs_to_snake_case
def resolve_most_published(
        *_, similarity: Literal['siblings', 'related'] = POST_SIBLINGS_FIELD,
        **kwargs):
    """
    Most ranking posts by number of similar stories published.

    Obtained by counting the number of similar stories (`sibling`, `related` posts)
    published about every post (using a GROUP_BY).
    """

    # use custom pipeline runtime instead of the default `agg_post_sum`
    # is callback for `agg_sum_to_schema` to call ie. `agg_sum(by, sum_by, **kwargs)`
    # sum_by, kwargs unused here, just for convenience
    agg_sum = lambda by, sum_by: \
        exec_agg_sum_pipeline(pipeline, **kwargs)

    # `by` here is not used, since this func uses a custom agg_sum/pipeline.
    # this only to satisfy the runtime args checks.
    by = Agg.GroupBy.siblings
    match = mkfilter(kwargs)

    # though MongoDB's `$size` op allows to count array column directly,
    # it cannot insert the root to the results. using below trick instead
    # https://stackoverflow.com/a/21721480.
    #
    # https://stackoverflow.com/a/57179240,  https://stackoverflow.com/a/25713818
    # pipeline = [
    #     {"$match": match},
    #     {"$project": {"_id": 1, f"{STAT_VALUE_FIELD}": {"$size": f"${similarity}"}}},
    #     {"$sort": {f"{STAT_VALUE_FIELD}": -1}},
    # ]

    pipeline = [
        {"$match": match},
        {"$project": {"_id": "$$ROOT", f"{similarity}": f"${similarity}"}},
        {"$unwind": f"${similarity}"},
        {"$group": {
            "_id": "$_id",
            f"{VALUE_FIELD}": {"$sum": 1}}},
        {"$project": {
            "_id": "$_id._id", f"{VALUE_FIELD}": 1,
            "doc": "$_id"}}
    ]

    return agg_sum_to_schema(
        by, agg_sum=agg_sum, gql_subfield=f"{NAME_FIELD}")


@query.field("mostOccurring")
@convert_kwargs_to_snake_case
def resolve_most_occurring(
        *_, similarity: Literal['siblings', 'related'] = POST_SIBLINGS_FIELD,
        **kwargs):
    """
    Count/Posts that harnessed the more interest across newspapers.
    Most occurring siblings/related posts that generated other posts
    Count/posts that share a similarity with any other post,
    within the scope of a given day (remember: similarity is computed daily)

    Obtained by taking the intersection of all `siblings` or `related` fields
    (so typically won't yield metaposts) that contain any given post, then rank by count.

    Usages:

        # group/count all metaposts that share a given post in their `related` field
        >>> resolve_most_intersecting(similarity=GroupBy.related, type="metapost")

        # group/count all metaposts that any given post contributed to generate.
        # remember, metapost were initially created from sibling posts.
        >>> resolve_most_intersecting(type="metapost")
    """
    by, sum_by = (Agg.GroupBy.siblings, Agg.SumBy.siblings) \
        if similarity == POST_SIBLINGS_FIELD \
        else (Agg.GroupBy.siblings, Agg.SumBy.related)

    return agg_sum_to_schema(
        by, sum_by=sum_by, gql_subfield=f"{NAME_FIELD}", **kwargs)


@query.field("categoriesCounts")
@convert_kwargs_to_snake_case
def resolve_categories_counts(*_, **kwargs):
    """
    Ordered mapping of post counts for each category
    in the input date range.
    Eg.
        [{'name': 'Carburants', 'value': 2 }, ...]
    """
    return agg_sum_to_schema(
        Agg.GroupBy.categories, gql_subfield=f"{NAME_FIELD}", **kwargs)


@query.field("tagsCounts")
@convert_kwargs_to_snake_case
def resolve_tags_counts(*_, **kwargs):
    """
    Ordered mapping of post counts for each tag
    """
    return agg_sum_to_schema(
        Agg.GroupBy.tags, gql_subfield=f"{NAME_FIELD}", **kwargs)


@query.field("countriesCounts")
@convert_kwargs_to_snake_case
def resolve_countries_counts(*_, **kwargs):
    """
    Ordered mapping of post counts for each tag
    """

    def mk_country(count):
        # FIXME: once refactored newsbot: pycountry -> python-babel,
        #  then must have country code ==  locale.territory
        locale = Locale.parse(f"und_{count[NAME_FIELD]}")
        assert count[NAME_FIELD] == locale.territory
        count["doc"] = {
            "country_code": locale.territory,
            "country_name": locale.get_territory_name('en'),
            "timezone": pytz.country_timezones(locale.territory)[0],
            "currency": get_territory_currencies(locale.territory)[0],
            "languages": [locale.get_language_name('en')]}
        return count

    counts = agg_sum_to_schema(
        Agg.GroupBy.countries, gql_subfield=f"{NAME_FIELD}", **kwargs)

    return map(mk_country, counts)


# FIXME: deleteme: obsolete code. not using service workers on frontend anymore.
# @query.field("stats")
@convert_kwargs_to_snake_case
def resolve_stats(*_, from_date=None, to_date=None, limit=None, recursive=False):
    """
    Compile stats for posts matching given date range and count.
    :returns dict: stats by action for all matched posts.

    Requires adding to GraphQL schema:
        `type Query {
            stats(from_date: String, to_date: String, limit:Int, recursive:Boolean): Stats
        }`
    """

    posts = list(engine.search(
        from_date=from_date, to_date=to_date,
        flatten=True, limit=limit
    ))

    stats = defaultdict(list)
    for key in POST_ACTIONS:
        action_stats = list(filter(None, map(
            lambda p: get_post_stats_for_action(format_doc(p), key, recursive=recursive),
            posts
        )))
        action_stats = list(chain.from_iterable(action_stats))
        stats[key] += action_stats

    return stats


@query.field("post")
@convert_kwargs_to_snake_case
def resolve_post(*_, post_id=None, adjacent=1):
    """
    Find the given post across all collections (days).
    Embeds #adjacent_posts previous/next posts.
    :param adjacent: number of previous/next posts to insert
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

    opts = {"match": {"_id": object_id}, "limit": 1,
            "adjacent": adjacent}
    posts = list(search_posts(**opts))
    if not len(posts):
        return

    return posts[0]


@query.field("posts")
@convert_kwargs_to_snake_case
def resolve_posts(*_, **kwargs):
    """
    List of posts across all collections matching given criteria.
    """
    post_filter = mkfilter(kwargs)
    if post_filter is None:
        return []
    posts = list(search_posts(match=post_filter, **kwargs))
    return posts


@query.field("categories")
@convert_kwargs_to_snake_case
def resolve_categories(*_, **kwargs):
    """ All categories across filtered day-collections """
    return engine.distinct('category')


@query.field("tags")
@convert_kwargs_to_snake_case
def resolve_tags(*_, **kwargs):
    """ All tags across filtered day-collections """
    return engine.distinct('tags')


def search_posts(
        days=None, days_from=None, days_to=None,
        limit=None, match=None, fields=None, exclude=None,
        adjacent=None,
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

    Other params, cf. `utils.find()`:

    :param flatten: whether to also return the collection with the post, as a tuple
        ie., returns [Post, ...]? or [(Post,Collection), ...]?
    :param adjacent: # of previous/next posts to also embed with every post.
        only adjacent posts of same `type` as given post will be included.
        None if should not include adjacent posts

    #TODO: better handling for POST_SIBLINGS_FIELD not found error??
    #TODO: engine.search to yield `Doc` instances directly

    """

    for post in engine.search(
            flatten=True, limit=limit, match=match, fields=fields, exclude=exclude,
            days=days, days_from=days_from, days_to=days_to
    ):
        yield expand_post(post, adjacent)


def expand_post(doc: Doc, adjacent=1):
    """
    Replace:
        { "siblings": [{"_id": <doc_id>, "score": <similarity_score>}, ...]}
        { "related": [{"_id": <doc_id>, "score": <similarity_score>}, ...]}
    with actual post

    """
    if not doc:
        return

    related_fields = POST_SIBLINGS_FIELD, POST_RELATED_FIELD
    adjacent_fields = POST_PREVIOUS_FIELD, POST_NEXT_FIELD

    return expand_doc(doc, related_fields, adjacent_fields, adjacent)


def expand_doc(doc: Doc, related_fields: Tuple[str], adjacent_fields: Tuple[str],
               adjacent=1):
    """
    Expands in-place docs relations and adjacencies.

    (a) patches doc's relations (pointed to by `related_fields`) into full docs
    (b) patches doc with `adjacent` adjacent documents (ie., before/next given doc)

        Drops relationships inside related docs to avoid expanding relations
    in a recursive manner.

    # TODO: replace by pipeline, be more efficient to transfer workload to Mongo

    :param doc: doc to expand
    :param adjacent_fields: previous and next field names as a 2-uple
    :param related_fields: fields to explode, each of which contain a `_id` key
            storing an ObjectId pointing to other docs in same collection
    :param Callable fmt_func:
    :param int adjacent: count of adjacent docs to retrieve and replace
    :return: same input doc, but with expanded relationships and adjacencies.
    """
    if not doc:
        return

    def _drop_relations(d: Doc):
        for x in related_fields:
            del d[x]
        return d

    def _expand_relations(to: Doc):
        """
        Expand in-place list [{"_id": <ObjectId>, ..}, ...] of related docs
        into full docs from same collection.
        Also inserts similarity scores with the `to` doc (`score` field).
        """
        for rel in related_fields:
            try:
                rel_docs = to.collection.find({
                    "_id": {"$in": list(map(lambda x: x["_id"], to[rel]))}, })

                # do NOT recurse, instead, drop the related fields
                # on expanded doc for every relation
                rel_docs = map(_drop_relations, rel_docs)

                # apply format func to expanded docs
                # inserts the similarity score with the mother post
                rel_scores = map(lambda x: {"score": x["score"]}, to[rel])
                to[rel] = list(map(lambda x: format_doc(x[0], update=x[1]), zip(rel_docs, rel_scores)))
            except KeyError:
                to[rel] = []
        return to

    def _expand_adjacent(to: Doc, type: str, count: int):
        """
        Fetch **count** docs adjacent to **to*

        :param Doc to: fetch adjacent docs
        :param type: type of post. eg., `metapost`, `metapost.default`, etc.
        :return:

        # TODO: add option to only load pre-selected fields on adjacent docs.
        # TODO: change `type` arg into query filter (more generic func)
                that can be moved to `daily.mongo`

        """
        if count:

            _mkfilter = lambda op: \
                {'type': {'$regex': f'{type}', '$options': 'i'},
                 '_id': {op: to.data["_id"]}}

            lookups = ({'op': '$lt', 'sort': [('_id', -1)]},
                       {'op': '$gt', 'sort': [('_id', 1)]})

            adj_docs = []
            for lookup in lookups:
                lookup_docs = to.collection.find(_mkfilter(lookup['op'])) \
                    .sort(lookup['sort']).limit(count)
                adj_docs += [list(map(compose(
                    format_doc, _drop_relations), lookup_docs))]

            previous_docs, next_docs = adj_docs
            previous_field, next_field = adjacent_fields
            to[previous_field] = previous_docs
            to[next_field] = next_docs

    # patch doc with relation fields exploded,
    # patch doc with `adjacent` adjacent docs within collection,
    _expand_relations(doc)
    _expand_adjacent(doc, doc[POST_TYPE_FIELD], adjacent)

    return format_doc(doc)


def mkfilter(kwargs):
    """
    Generate a MongoDB posts query filter from kwargs
    # TODO: typings for kwargs
    """

    post_filter = {}

    # https://stackoverflow.com/a/52018277
    post_type = kwargs.pop('type', None)
    if post_type:
        post_filter.update({'type': {
            '$regex': f'{post_type}', '$options': 'i'}})

    has_videos = kwargs.pop('has_videos', None)
    if has_videos:
        post_filter.update({'videos': {
            '$exists': 'true', '$type': 'array', '$ne': []}})

    countries = kwargs.pop('countries', None)
    if countries is not None:
        countries = list(set(countries))
        if len(countries) == 0:
            return
        post_filter.update({'country': {
            '$in': countries}})

    categories = kwargs.pop('categories', None)
    if categories is not None:
        categories = list(set(categories))
        if len(categories) == 0:
            return
        post_filter.update({'category': {
            '$in': categories}})

    post_ids = kwargs.pop('post_ids', None)
    if post_ids is not None:
        post_ids = list(set(post_ids))
        if len(post_ids) == 0:
            return
        post_filter.update({'_id': {
            '$in': [ObjectId(x) for x in post_ids]}})

    return post_filter


#
# AGGREGATION
# ===========
# TODO: move all below aggregation utils to the `daily.mongo` module/class.
#


def agg_post_sum(by: Agg.GroupBy, sum_by: Agg.SumBy = Agg.SumBy.count, **kwargs):
    """
    Runs the default aggregation pipeline, which sums or counts posts grouped by
    a given column. Column is specified as one of the field paths stored in the
    `Aggregation.GroupBy` enum values; eg.: PostBy.tag, PostBy.categories, etc.

    Returns a ordered mapping of posts counts by _id DESC,
    NOT in GraphQL format !

        eg. {"Politique": 322, "Culture": 153, ...}

    """
    # TODO: move func to `daily_query.mongo.py`.
    #   this code must stay engine agnostic

    unwind, relation = Agg.extract_fields(by)

    match = mkfilter(kwargs)  # <- FIXME: this alters kwargs. is desirable?
    match_filter = [{"$match": match}] if match else []

    # following list fields must be unwinded first
    # eg., duplicate each post as many times as having each tag
    unwind_relation = [{"$unwind": {
        "path": f"${unwind}", "preserveNullAndEmptyArrays": True}}
    ] if unwind else []

    # also expand groupby field if it is a foreign key to self
    # performs a SQL self-join using aka. $lookup
    inflate_doc = lambda collection: [
        {"$lookup": {
            "from": str(collection), "localField": "_id",
            "foreignField": f"_id", "as": f"doc"}},
        {"$unwind": f"$doc"}
    ] if relation else []

    # https://mongoplayground.net/p/8WYDmj740WF
    pipeline = lambda collection: [
        *match_filter,
        *unwind_relation,
        {"$group": {
            "_id": f"${by.value}",
            f"{VALUE_FIELD}": {"$sum": 1 if sum_by == Agg.SumBy.count
            else f"${sum_by.value}"}
        }},
        *inflate_doc(collection),
        {"$sort": {f"{VALUE_FIELD}": -1}},
        {"$project": {"_id": 1, f"{VALUE_FIELD}": 1, "doc": 1}}
    ]

    return exec_agg_sum_pipeline(pipeline, **kwargs)


def exec_agg_sum_pipeline(pipeline, **kwargs):
    """ Run MongoDB pipeline """

    results = defaultdict(lambda: defaultdict(int))

    for row, collection in engine.aggregate(pipeline, **kwargs):

        count = row[VALUE_FIELD]
        by_value = row["_id"]

        # skip rows with empty grouped by column
        # also insert root doc if available
        # do NOT yield here: cross-collection cumulated results required!
        if by_value:
            results[by_value]["sum"] += count
            if "doc" in row:
                results[by_value]["doc"] = Doc(collection, row['doc'])  # noqa

    # fix for ranking by value DESC across the entire dataset (all collections),
    # since the pipeline's $sort does this only per collection
    results = dict(sorted(results.items(),
                          key=lambda item: item[1]["sum"], reverse=True))
    return results


def agg_sum_to_schema(by, sum_by=Agg.SumBy.count, agg_sum=agg_post_sum, gql_subfield=None, **kwargs):
    """ Adapt results from `agg_post_sum()` to an array of dicts
        suitable for returning as the GraphQL type `DocStat` (aggregate).

        Eg., following GraphQL query:
            query($type:String="metapost.featured", $countries:[String])  {
              categoriesCounts(type:$type, countries:$countries) {
                category
                postsCount } }

        results in the function being called like so:
            agg_sum_to_schema(GroupBy.categories, 'category', **kwargs)

        which yields:
              { "data": {  "categoriesCounts": [
                    {"category": "Politique", "postsCount": 1}, ...
              ]}}
    """
    results = agg_sum(by, sum_by, **kwargs)
    results = [{
        gql_subfield or by.name: k,
        VALUE_FIELD: v["sum"],
        **({"doc": expand_post(v.get("doc"))} if v.get("doc") else {})
    } for k, v in results.items()]
    return results


def format_doc(post, update=None, exclude=None) -> dict:
    """
    Format post raw database data in-place for use by frontends
    - replaces database's `bson.ObjectId` with str `id` field
    - insert the `is_meta` boolean that tells whether is a metapost

    :param Doc post: post data
    :param dict update: additional data
    :param Iterable[str] exclude: fields to remove
    """
    post['id'] = str(post['_id'])
    del post['_id']

    post[POST_IS_META_FIELD] = post[POST_TYPE_FIELD].startswith(METAPOST)

    if update:
        assert isinstance(update, dict), "`update` must be dict"
        post.update(update)

    if exclude:
        for f in exclude:
            del post[f]

    # make Doc object json-serializable
    return dict(post)
