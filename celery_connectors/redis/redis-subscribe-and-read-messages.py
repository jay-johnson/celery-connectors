#!/usr/bin/env python

import os
import sys
import time
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
name = "redis-subscriber"

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

while True:
    msg = app.wait_for_message_on_key(num_seconds=1, key=queue_name)
    if msg:
        log.info("Received msg: " + str(msg))
# end of infinite while loop - stop with ctrl + c
