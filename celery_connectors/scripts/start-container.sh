#!/bin/bash

echo ""
date

cd /opt/celery_connectors
source /opt/celery_connectors/venv/bin/activate

echo "Starting Celery=${APP_NAME} loglevel=${LOG_LEVEL}"
celery worker -A run_rabbitmq_subscriber -c 3 --loglevel=${LOG_LEVEL} -n ${APP_NAME} -Ofair
