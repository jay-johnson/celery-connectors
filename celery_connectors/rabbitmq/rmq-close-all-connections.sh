#!/bin/bash

host="localhost"
port=15672
user=rabbitmq
pw=rabbitmq
container_name=celrabbit1

echo ""
echo "Closing all connections for broker=${host}:${port}"
echo ""
if [[ -f /tmp/.all-rabbit-connections.txt ]]; then
    rm -f /tmp/.all-rabbit-connections.txt
fi
rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} -f tsv -q list connections name > /tmp/.all-rabbit-connections.txt
while read -r name; do rabbitmqadmin.py --host=${host} --port=${port} --username=${user} --password=${pw} -q close connection name="${name}"; done < /tmp/.all-rabbit-connections.txt
if [[ -f /tmp/.all-rabbit-connections.txt ]]; then
    rm -f /tmp/.all-rabbit-connections.txt
fi
echo ""
echo ""
