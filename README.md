# leeram-news/newsapi


## Quick start

### Requirements

* running MongoDb instance (required by `newsbot`, `newsapi`)

```shell
docker run -d -p 27017:27017 --name mongodb \
  -v pgdata:/var/lib/postgresql/data \
#  -e MONGO_INITDB_ROOT_USERNAME=techu \
#  -e MONGO_INITDB_ROOT_PASSWORD=techu0910! \
  mongo:latest
```

### Env prep.

```shell
cd ../newsapi
python -m venv venv
source venv/bin/activate
pip install -U pip pip-tools
```

## Install Dependencies

* Already included in requirements.
Just run `pip-sync src/requirements/dev.txt` 
(or `prod.txt` for Production). Eg:

```shell
pip-sync src/requirements/dev.txt  
```
* To re-generate dependencies files:

```shell
pip install -U pip pip-tools
pip-compile --output-file=requirements/dev.txt --resolver=backtracking requirements/in/dev.txt
```

## Standalone execution

```shell
FLASK_APP=src/app/run:app \
MONGO_URI=mongodb://localhost:27017/scraped_news_db \
flask run -h 0.0.0.0 -p 5100 --debugger
```

### Run as Docker stack

* Docker-compose
Database (PostgresSQL) + Flask API server + CMS (Strapi?)
Compose file: `Leeram/docker/docker-compose.yml`
Ensure exists env file: `src/.env` with following defaults:

```shell
COMPOSE_PROJECT_NAME=leeram
MONGO_URI=mongodb://db:27017/scraped_news_db
docker-compose up 
```

### Debug from shell

```shell
# spawn a shell 
FLASK_APP=src/app/run:app \
MONGO_URI=mongodb://localhost:27017/scraped_news_db \
flask shell

from app.posts.queries import search_posts

# kill all debug instances
lsof -i tcp:5100 | xargs kill
```

## Prod (on GCP)

* Getting [ready for GCP](./doc/gcloud-init.md). Optional, do once per project) 
* Deploy on local KinD Kubernetes cluster
* Deploy on [GKE](gke.md)
* Run as a [Google Cloud Run Service](./doc/cloudrun.md).


