#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker

echo "Starting persistence redis and rabbitmq"
docker-compose -f persistence_redis_and_rabbitmq.yml up -d

exit 0
