#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker

echo "Starting redis and rabbitmq"
docker-compose -f redis_and_rabbitmq.yml up -d

exit 0
