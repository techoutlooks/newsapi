import random
import datetime

import mongomock
import pytest


# https://stackoverflow.com/a/51994349
@pytest.fixture(autouse=True)
def mongo(mocker):
    mongo = mongomock.MongoClient()

    def fake_mongo():
        return mongo

    mocker.patch('newsapi.app.db.mongo', fake_mongo)


# @pytest.fixture(autouse=True)
# def get_db(mocker, mongo):
#     yield mongo.db
#

@pytest.fixture(scope="module", params=["2021-08-22", ])
def from_date(req):
    yield req.param


@pytest.fixture(scope="module", params=["2021-08-22", ])
def to_date(req):
    yield req.param


def random_date(start_date, end_date):
    # start_date = datetime.date(2020, 1, 1)
    # end_date = datetime.date(2020, 2, 1)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + datetime.timedelta(days=random_number_of_days)


def random_date_range(start_date, end_date):
    pass