FROM python:3.6-alpine

RUN apk add --update \
    python \
    python-dev \
    py-pip \
    build-base \
    curl \
    curl-dev \
    bash \
    libffi-dev \
    net-tools \
    heimdal-telnet \
    openssl \
    openssl-dev \
    vim \
  && pip install virtualenv

RUN mkdir -p -m 777 /opt/celery_connectors /opt/shared /opt/logs /opt/data /opt/configs
WORKDIR /opt/celery_connectors

COPY celery_connectors-latest.tgz /opt/celery_connectors
COPY ./docker/bashrc /root/.bashrc

RUN cd /opt/celery_connectors && tar xvf celery_connectors-latest.tgz && ls /opt/celery_connectors

RUN echo "Starting Build"

RUN cd /opt/celery_connectors \
  && virtualenv -p python3 /opt/celery_connectors/venv \
  && source /opt/celery_connectors/venv/bin/activate \
  && pip install -e .

ENV START_SCRIPT /opt/celery_connectors/celery_connectors/scripts/start-container.sh 
ENV LOG_DIR /opt/logs
ENV CONFIG_DIR /opt/logs
ENV DATA_DIR /opt/logs

ENTRYPOINT bash /opt/celery_connectors/celery_connectors/scripts/start-container.sh
