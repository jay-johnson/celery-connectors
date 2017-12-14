#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq

echo ""
echo "Listing Bindings broker=${host}:${port}"
echo ""
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} list bindings source routing_key destination
echo ""
