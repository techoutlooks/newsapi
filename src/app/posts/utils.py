import re


# CONSTS
# ======

POST_ENTITY_NAME = 'post'

post_id_pattern = re.compile(f"(?<={POST_ENTITY_NAME}\/)\w*")


# FUNCS
# ======


def parse_post_url(url):
    """ Get kwargs {id: <post_id>, } from url """

    kwargs = {}

    # first match only (re.search)
    id_match = post_id_pattern.search(url)

    kwargs["id"] = id_match.group(0) if id_match else None
    return kwargs


def get_post_stats_for_action(post, action, recursive=True):
    """
    Get post (post) stats matching **action**
    eg., clicks on post or linked posts (HTML anchors in post pages).

    :param post:
    :param action: user action eg. "click", etc.
    :param recursive: if True, also gets stats for **action**'s on html elements
            embedded inside post page (`root` thereafter)
            eg. gets stats for clicks on monitored links inside page (url).
            if False, get single stat for root page (url) only.

    :return:
    """
    post_stats = post.get("stats")
    action_stats = post_stats.get(action) \
        if post_stats else None

    # checks in stat is for action that opened root page,
    # not on links embedded inside root page (recursive mode)
    def is_root_stat(stat, post_id):
        url = stat["on"]["name"]
        stat_post_id = parse_post_url(url)["id"]
        return stat_post_id == post_id

    # not recursive? get stats for post url (root) only.
    # filters out embedded links stats from posts stats, for all actions
    if action_stats:
        if not recursive:
            action_stats = list(filter(
                lambda s: is_root_stat(s, post["id"]),
                action_stats
            ))

    return action_stats



