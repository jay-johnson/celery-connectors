#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq

echo ""
echo "Listing Channels broker=${host}:${port}"
echo ""
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} list channels name connection number confirm consumer_count messages messages_unacknowledged messages_uncommitted messages_unconfirmed acks_uncommitted prefetch_count global_prefetch_count
echo ""
