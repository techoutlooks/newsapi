import os
import datetime


DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = f'{DATE_FORMAT} %H:%M:%S'


mk_date = lambda x=None: mk_datetime(x, True)


def mk_datetime(input=None, date_only=False) -> datetime.datetime:
    """
    Create a datetime obj from anything.
    ::param input: `str` date/time, `datetime.date` or `datetime.datetime`
    ::returns corresponding `datetime` obj,
              or the current datetime if no input was passed in.
    """
    date_time = input
    if not input:
        date_time = datetime.datetime.now()     # careful, now() is both datetime and date!
    if isinstance(date_time, datetime.date):
        if not isinstance(date_time, datetime.datetime):
            date_time = str(date_time)
    if isinstance(date_time, str):
        if len(date_time.split()) == 1:
            date_time = f"{str(date_time)} 00:00:00"
        date_time = str(date_time).split('.')[0]
        date_time = datetime.datetime.strptime(date_time, DATETIME_FORMAT)
    if date_only:
        date_time = date_time.date()
    return date_time


def get_env_variable(name) -> str:
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)

