
## Deploy to GKE

1. Assumes project is GCP [ready](gcloud-init.md)
2. Build image -> GCP Artifact Registry (Docker Registry obsolete)

    ```shell
   cd ../src
    export TAG=1.0 REGISTRY=localhost:5001
    docker build . -t $REGISTRY/newsapi:$TAG  --no-cache # --pull
    ```

3. Deploy to GKE

    ```shell
    export TAG=1.0 REGISTRY=localhost:5001
    export REPOSITORY="leeram-docker" PROJECT=leeram
   
    docker tag localhost:5001/newsapi:$TAG europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsapi:$TAG
    docker push europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsapi:1.0
    ```

