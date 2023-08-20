# Getting started with GCP 

Optional, do once per project. 


## Setup GCP CLI locally

- Install and authenticate `gcloud` CLI locally
    ```shell
    curl https://sdk.cloud.google.com | bash
    gcloud init
    ```

- Set few useful env vars before proceeding. \
  Note: Get valid project id from: `gcloud config list`
    ```shell
    
    # newsbot 
    DB_URI='mongodb+srv://techu:techu0910!@cluster0.6we1byk.mongodb.net/scraped_news_db?retryWrites=true&w=majority'
    
    # gcloud
    REGION=europe-west1
    PROJECT_ID=leeram
    BOT_IMAGE_NAME=newsbot:v1
    SERVICE_ACCOUNT=local-docker-service
    GCP_KEY_PATH=~/Devl/Projects/ARISE/key.json
    ```

- Set global env vars
    ```shell
    gcloud config set core/project $PROJECT_ID
    gcloud config set run/region $REGION
    ```


## GCP Service Account

Goal:

* Create a service account (required to make requests to Google APIs) with necessary permissions.
* Enable required GCP apis

Steps:

1. Create new service account with appropriate permissions,
   associate it with the project.
   Could have also used a single `--role roles/owner` \
   Refs: [1](https://cloud.google.com/sdk/gcloud/reference/projects/add-iam-policy-binding)

    ```shell
    gcloud iam service-accounts create local-docker-service 
    PROJECT_ID=leeram 
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member "serviceAccount:${SERVICE_ACCOUNT}@$PROJECT_ID.iam.gserviceaccount.com" \
        --role "roles/storage.admin" \
        --role "roles/run.admin"
    ```

2. Create and download service account key.json from CGP's IAM service.
   (preferably outside git repo), and export it locally.
    ```shell
    gcloud iam service-accounts keys create ${GCP_KEY_PATH} \
        --iam-account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
   
    export GOOGLE_APPLICATION_CREDENTIALS=${GCP_KEY_PATH}
    ```

3. Enable cloud APIs: 
    ```shell
    gcloud services enable \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        cloudscheduler.googleapis.com
    ```
   
## Authenticate Docker (optional)

Authenticate Docker with the Container Registry service on GCR. \
Refs: [1](https://cloud.google.com/container-registry/docs/advanced-authentication)

    ```shell
    cat ${GCP_KEY_PATH} | docker login -u _json_key --password-stdin https://grc.io
    ```
   
    Alternate method :
    ```shell 
    gcloud auth configure-docker gcr.io
    ```


## Docs:

 [1](https://cloud.google.com/run/docs/execute/jobs),
 [2](https://cloud.google.com/run/docs/quickstarts/jobs/build-create-python),
 [3](https://github.com/GoogleCloudPlatform/jobs-demos),
