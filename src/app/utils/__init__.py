from copy import deepcopy
from functools import reduce
from environs import Env


__all__ = (
    "compose", "setdict", "deepmerge",
    "get_env",
)


# `read_env()` is to allow reading from .env file
env = Env()
env.read_env()


compose = lambda *fns: reduce(lambda f, g: lambda t: f(g(t)), fns)


def setdict(d, path, value):
    """
     Set dict's nested attribute without messing with sibling keys.
    TODO: reframe to use reducer
    """
    dd = d
    keys = path.split('.')
    latest = keys.pop()
    for k in keys:
        dd = dd.setdefault(k, {})
    dd[latest] = value


def deepmerge(a: dict, b: dict, inplace=False) -> dict:
    """
    https://gist.github.com/angstwad/bf22d1822c38a92ec0a9?permalink_comment_id=4038517#gistcomment-4038517
    """

    result = a if inplace else deepcopy(a)
    for bk, bv in b.items():
        av = result.get(bk)
        if isinstance(av, dict) and isinstance(bv, dict):
            result[bk] = deepmerge(av, bv)
        else:
            result[bk] = deepcopy(bv)
    return result


def get_env(name, *args, coerce=None) -> str:
    """
    Get the value for environment variable <name>.
    Takes the default value as only positional arg.
    Raises variable <name> is not set and no default is supplied.

    * Uses environs => dotenv packages for env parsing.

    :param str name: env name
    :param bool|str coerce: whether to require env var to assume a certain type
        coerce==False: dismiss type casting. similar to using `env()`
        coerce==True: auto-detection of casting type
        type(coerce)==string: requires type casting method name
            eg. 'int'|'str'|'bool'|'dict', etc.
            cf. https://pypi.org/project/environs/#supported-types
    """

    # at most single arg after env name
    assert len(args) < 2, \
        "`get_env()` supports at most two positional arguments: " \
        "eg., get_env('ENV_VAR_NAME', default_value, coerce=dict)"

    # coerce must either be supported casting type from the environs package,
    # or coerce==True => sniff cast type from default value (auto mode)
    typecast = coerce
    if coerce:
        if len(args) and coerce is True:
            default = args[0]
            typecast = type(default).__name__
        assert hasattr(env, typecast), \
            f"{coerce} is no supported type-casting methods of Env!" \
            f"Cf. https://pypi.org/project/environs/#supported-types."

    _get_env = getattr(env, typecast) \
        if coerce else env

    return _get_env(name, *args)
