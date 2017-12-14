#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq

echo ""
echo "Listing Connections broker=${host}:${port}"
echo ""
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} list connections name state channels timeout
echo ""
