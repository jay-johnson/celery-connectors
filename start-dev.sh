#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker/dev

compose_file="rabbitmq-celery-only-consume.yml"

echo "Starting celery-connector with compose_file=${compose_file}"
docker-compose -f $compose_file up -d

exit 0
