#!/bin/bash

echo ""
date
echo "Starting rabbitmq subscriber"

# this assumes the current directory is the repository's home dir
export LOG_LEVEL=DEBUG
export LOG_CFG=./celery_connectors/log/logging.json
export APP_NAME="rabbitmq_subscriber_$(date +"%Y-%m-%d-%H-%M-%S")"

celery worker -A run_rabbitmq_subscriber -c 3 --loglevel=${LOG_LEVEL} -n ${APP_NAME} -Ofair
