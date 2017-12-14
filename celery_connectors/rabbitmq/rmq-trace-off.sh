#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq
container_name=celrabbit1

echo ""
echo "Turning off tracing for broker=${host}:${port}"
echo ""
docker exec -it ${container_name} rabbitmqctl trace_off
echo ""
