#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq

echo ""
echo "Listing Queues broker=${host}:${port}"
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} list queues name consumers messages messages_ready messages_unacknowledged
echo ""
