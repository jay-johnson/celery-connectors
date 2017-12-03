#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq

echo ""
echo "Listing Exchanges broker=${host}:${port}"
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} list exchanges name type
echo ""
