#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq
container_name=celrabbit1

echo ""
echo "Getting Status for broker=${host}:${port}"
echo ""
docker exec -it ${container_name} rabbitmqctl status
echo ""
echo "Generating Report for broker=${host}:${port}"
echo ""
docker exec -it ${container_name} rabbitmqctl report
echo ""
echo "Getting Environment for broker=${host}:${port}"
echo ""
docker exec -it ${container_name} rabbitmqctl environment
echo ""
echo ""
