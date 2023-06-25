# Prod (GCR, ie. Google Cloud Run)

### Set env vars

- Set few useful env vars before proceeding. \
  Note: Ensure of correct project id from: `gcloud config list`. 
  Note: `gcloud projects list` to see all projects.
    ```shell
    # newsapi 
    MONGO_URI='mongodb+srv://techu:techu0910!@cluster0.6we1byk.mongodb.net/scraped_news_db?retryWrites=true&w=majority'
    PORT=5000

    # gcloud
    REGION=europe-west1
    PROJECT_ID=leeram
    IMAGE_NAME=newsapi:v1
    SERVICE=newsapi
    SERVICE_ACCOUNT=local-docker-service
    GCP_KEY_PATH=~/Devl/Projects/ARISE/key.json
    ```
  
### Build the `newsapi` service

   
1. Build image, eg. `gcr.io/leeram/newsapi:v1` remotely
    ```shell
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME .
    ```

2. Create service `newsapi` (runs every 20mn)
    ```shell
    gcloud run deploy $SERVICE --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
        --update-env-vars MONGO_URI=$MONGO_URI \
        --port $PORT \
        --allow-unauthenticated
    ```

3. Run the job
    ```shell
    gcloud beta run jobs execute newsbot
    ```

### Misc

* Check image
    ```shell
    gcloud container images list-tags gcr.io/$PROJECT_ID/$SERVICE
    ```

* Describe the service
    ```shell
    gcloud run services describe $SERVICE
    ```

* Update memory
```shell
gcloud beta run jobs update newsbot --memory 4Gi
```

* Update env vars
    ```shell
    gcloud run services update $SERVICE \
        --update-env-vars MONGO_URI=$MONGO_URI
    ```

* Delete job
```shell
gcloud beta run jobs delete newsbot
```

