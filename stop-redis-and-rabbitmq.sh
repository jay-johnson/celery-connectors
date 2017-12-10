#!/bin/bash

# this assumes docker is running and docker-compose is installed

cd docker

echo "Stopping redis and rabbitmq"
docker-compose -f redis_and_rabbitmq.yml stop

if [[ "$?" == "0" ]]; then
    docker rm celredis1 celrabbit1 celflowerrabbit celflowerredis >> /dev/null 2>&1
fi

exit 0
