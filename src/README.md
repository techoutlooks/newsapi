


# Dependencies

Already included in requirements.
Just run `pip-sync src/requirements/dev.txt` (or `prod.txt` for Production)

```shell

pip install flask Flask-PyMongo \
    ariadne
```

# Standalone

```shell
export POSTGRES_URL=localhost:5432;\
POSTGRES_USER=postgres;POSTGRES_PASSWORD=techu0910!;POSTGRES_DB=analytics

```

# Docker stack

Database (PostgresSQL) + Flask API server + CMS (Strapi?)
Compose file: `src/docker-compose.yml`
Env file: `src/.env` exists with following defaults:
```shell
COMPOSE_PROJECT_NAME=arise-news
MONGO_URI=mongodb://db:27017/scraped_news_db
```


```shell

# kill all debug instances
lsof -i tcp:5100 | xargs kill
```