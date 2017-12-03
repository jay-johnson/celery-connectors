#!/usr/bin/env python

import os
import sys
import uuid
import json
import logging
from celery_connectors.logging.setup_logging import setup_logging
from celery_connectors.redis.redis_json_application import RedisJSONApplication

port = 6379
host = os.getenv("ENV_REDIS_HOST", "localhost").strip().lstrip()
db = int(os.getenv("ENV_REDIS_DB_ID", 0))
# if set to empty string use password=None
redis_pw = os.getenv("ENV_REDIS_PASSWORD", "")
queue_name = os.getenv("Q_1", "reporting.accounts").strip().lstrip()
name = "redis-producer"

setup_logging()

log = logging.getLogger(__file__)

log.info("START - {} - Sending messages to redis={}:{}/{} queue={}".format(name,
                                                                           host,
                                                                           port,
                                                                           db,
                                                                           queue_name))

if str(redis_pw) == "":
    redis_pw = None

app = RedisJSONApplication(name, redis_address=host, redis_port=port, redis_queue=queue_name, logger=log)
app.connect()

max_msgs = 1000
msgs = []
for x in range(0, max_msgs):
    msgs.append(str(x) + "=" + str(uuid.uuid4()).replace("-", ""))

for msg in msgs:
    payload = {"body": msg,
               "properties": {"delivery_tag": 1,
                              "delivery_info": {"routing_key": queue_name, "exchange": queue_name}}}
    app.put_into_key(queue_name, payload)
# end of for all to send

log.info("END - {} - Sending messages={} to redis={}:{}/{} queue={}".format(max_msgs,
                                                                            name,
                                                                            host,
                                                                            port,
                                                                            db,
                                                                            queue_name))
