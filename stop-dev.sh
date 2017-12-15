#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker/dev

compose_file="rabbitmq-celery-only-consume.yml"
echo "Stopping celery-connectors with compose_file=${compose_file}"
docker-compose -f ${compose_file} stop

if [[ "$?" == "0" ]]; then
    docker rm worker >> /dev/null 2>&1
fi

exit 0
