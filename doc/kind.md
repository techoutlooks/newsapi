

1. Build & push image to local docker registry:

```shell
export REGISTRY=localhost:5001 TAG=v1
docker build . -t $REGISTRY/newsapi:$TAG && docker push $REGISTRY/newsapi:$TAG
```