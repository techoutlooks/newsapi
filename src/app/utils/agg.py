from enum import Enum


class Aggregate:
    """
    Grouping posts by field value.
    <gql_subfield_name> = <db_field-a-path>

    eg. `sibling = "siblings._id"` to first unwind the `siblings` array in each post,
        before grouping them posts by their `siblings._id` path.
        $count, $sum operations following $group (group by) will return their result
        under the enum's name field, eg. `sibling`.

    """

    class GroupBy(Enum):

        # non-array fields
        countries = "country"
        categories = "category"

        # array fields
        # require unwinding first, prior to grouping by
        tags = "tags"
        siblings = "siblings._id"
        related = "related._id"

    class SumBy(Enum):
        """ Aggregate functions
        that it is possible to run after a group by clause
        """
        count = 1
        siblings = "siblings.score"
        related = "related.score"

    PLURAL_FIELDS = [GroupBy.tags.name, GroupBy.siblings.name, GroupBy.related.name]

    @classmethod
    def extract_fields(cls, by):
        unwind, relation = None, None

        fields = by.value.rsplit('.', 1)
        if by.name in cls.PLURAL_FIELDS:
            unwind = fields[0]
        if len(fields) == 2:
            relation = fields[1]

        return unwind, relation

