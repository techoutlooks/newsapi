# Push to local kind-registry:
# export REGISTRY=localhost:5001 TAG=v1
# docker build . -t $REGISTRY/newsapi:$TAG && docker push $REGISTRY/newsapi:$TAG
FROM python:3.9

RUN mkdir -p /flask-app
WORKDIR /flask-app

# Copy files
COPY requirements/prod.txt ./requirements.txt
COPY app ./app
COPY app/schema.graphql ./

# Install packages
RUN python -m pip install pip-tools
RUN python -m piptools sync

# Run flask app
EXPOSE 5000
ENV FLASK_APP="app" FLASK_DEBUG=1 FLASK_ENV=docker

# Development
#CMD ["flask", "run", "-h", "0.0.0.0"]

# Production
# https://flask.palletsprojects.com/en/2.3.x/deploying/gunicorn/
#CMD gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.run:app"]