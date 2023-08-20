
# db fields

from daily_query.constants import FETCH_BATCH

POST_FETCH_LIMIT = FETCH_BATCH

POST_SIBLINGS_FIELD = "siblings"
POST_RELATED_FIELD = "related"
POST_PREVIOUS_FIELD = 'previous'
POST_NEXT_FIELD = 'next'
POST_STATS_FIELD = 'stats'
POST_TYPE_FIELD = 'type'
POST_IS_META_FIELD = 'is_meta'


METAPOST = 'metapost'
POST_ACTIONS = ["clicks"]


# TODO: to enum `DocStat` mapping to graphql type `DocStat`
# expected GraphQL subfields,
# and such that appear in as dynamic field names in pipelines
NAME_FIELD = "name"
VALUE_FIELD = "value"

