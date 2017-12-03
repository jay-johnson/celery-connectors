#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker

echo "Stopping redis and rabbitmq"
docker-compose -f redis_and_rabbitmq.yml stop

exit 0
