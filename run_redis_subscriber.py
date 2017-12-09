#!/usr/bin/env python

import logging
from celery import Celery
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.subscriber import Subscriber

setup_logging()

name = "run-redis-subscriber"

log = logging.getLogger(name)

log.info("Start - {}".format(name))


recv_msgs = []


def handle_message(body, message):
    log.info(("callback received msg "
              "body={}")
             .format(body))
    recv_msgs.append(body)
    message.ack()
# end of handle_message


# Initialize Celery application
ssl_options = {}
conn_attrs = {"task_default_queue": "celery.redis.sub",
              "task_default_exchange": "celery.redis.sub"}
app = Celery()
sub = Subscriber("redis-subscriber",
                 ev("BROKER_URL", "redis://localhost:6379/0"),
                 app,
                 ssl_options,
                 **conn_attrs)


# Now consume:
queue = "reporting.accounts"
sub.consume(callback=handle_message,
            queue=queue,
            exchange=None,
            routing_key=None)

log.info("End - {}".format(name))
