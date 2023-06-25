import datetime

from ariadne import convert_kwargs_to_snake_case, ObjectType
from daily_query.constants import FETCH_BATCH
from daily_query.mongo import Collection

from app.database import db
from app.routes import query

DEFAULT_SPORTS_IDS = [102, 106]


class SportSchedule(Collection):
    """
    Querying sports schedules from the database
    """

    sport: str = None

    @property
    def season(self):
        y = datetime.date.today().year
        this_season = f"{y}-{y + 1}"
        return getattr(self, '_season', this_season)

    @season.setter
    def season(self, value: str):
        setattr(self, '_season', value)

    def __init__(self, sport=None, season=None):
        super().__init__(db_or_uri=db)
        self.sport = sport
        self.season = season


@query.field("sportsSchedule")
@convert_kwargs_to_snake_case
def resolve_schedule(*_, sport, season=None, limit=FETCH_BATCH):
    """
    Retrieve upcoming schedule (next events) for given sport
    :param limit:
    :param str sport: eg. Soccer=102, Basketball=106.
    :param str season: eg. 2022-2023
    """
    pipelines = [
        {"$match": {"dateEvent": {
            "$gte": str(datetime.date.today())}}},
        {"$limit": limit},
        {"$project": {
            "sport": "$strSport", "season": "$strSeason",
            "event": "$strEvent", "league": "$strLeague",
            "venue": "$strVenue", "time": "$strTimestamp",
            "city": "$strCity", "country": "$strCountry",
            "status": "$strStatus", "postponed": "$strPostponed",
            "home_team": "$strHomeTeam", "away_team": "$strAwayTeam",
            "thumb": "$strThumb"}}
    ]
    events = SportSchedule(sport=sport, season=season)
    data = events(sport).aggregate(pipelines)
    return data


