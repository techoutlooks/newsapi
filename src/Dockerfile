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
CMD ["flask", "run", "-h", "0.0.0.0"]


## start the uvicorn server on $PORT variable
#CMD exec uvicorn routes:app --host 0.0.0.0 --port $PORT