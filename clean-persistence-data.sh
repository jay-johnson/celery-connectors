#!/bin/bash

echo ""
echo "Using root to delete persistence directories: ./docker/data/rabbitmq/ ./docker/data/redis and logs: ./docker/logs/rabbitmq ./docker/logs/redis and files: ./docker/data/rabbitmq/.erlang.cookie"
echo ""

loc="./docker/data/rabbitmq ./docker/logs/rabbitmq ./docker/data/redis ./docker/logs/redis ./docker/data/rabbitmq/.erlang.cookie"
for d in ${loc}; do
    if [[ -e ${d} ]]; then
        echo " - deleting=${d}"
        last_status=1
        if [[ -f ${d} ]]; then
            rm -rf ${d}
            last_status=$?
        elif [[ -d ${d} ]]; then
            rm -rf ${d}/*
            last_status=$?
        fi
        if [[ "${last_status}" != "0" ]]; then
            echo ""
            echo ""
            echo "Failed to delete: ${d}"
            echo "Please make sure to run this tool with sudo or as root."
            echo "This is because docker-compose creates files and directories as the host's root user with these vanilla containers."
            echo ""
            echo ""
            exit 1
        fi
    fi
done

exit 0
