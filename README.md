

## Env prep.

```shell
pip install -U pip pip-tools
pip-compile --output-file=requirements/dev.txt --resolver=backtracking requirements/in/dev.txt
```

## Install Dependencies

Already included in requirements.
Just run `pip-sync src/requirements/dev.txt` (or `prod.txt` for Production)

```shell

pip install flask Flask-PyMongo \
    ariadne
```

## Standalone execution

```shell
MONGO_URI=mongodb://localhost:27017/scraped_news_db
```

## Run as Docker stack

Database (PostgresSQL) + Flask API server + CMS (Strapi?)
Compose file: `LEERAM/backend/docker-compose.yml`
Ensure exists env file: `src/.env` with following defaults:

```shell
COMPOSE_PROJECT_NAME=leeram
MONGO_URI=mongodb://db:27017/scraped_news_db
```

## Debug from shell

```shell
# spawn a shell 
FLASK_APP=src/app/run:app \
MONGO_URI=mongodb://db:27017/scraped_news_db \
flask shell

from app.posts.queries import search_posts

# kill all debug instances
lsof -i tcp:5100 | xargs kill
```

# Prod (on GCP)

* Getting [ready for GCP](./doc/gcloud-init.md). Optional, do once per project) 
* Run project as a [gcloud service](./doc/gcloud.md).


