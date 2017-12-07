#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import logging
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.kombu_subscriber import KombuSubscriber

setup_logging()

name = "kombu-redis-subscriber"

log = logging.getLogger(name)

log.info("Start - {}".format(name))


recv_msgs = []


def handle_message(body, message):
    log.info("kombu.subscriber recv msg props={} body={}".format(message, body))
    recv_msgs.append(body)
    message.ack()
# end of handle_message


# Initialize KombuSubscriber
ssl_options = {}
sub = KombuSubscriber("kombu-redis-subscriber",
                      ev("BROKER_URL", "redis://localhost:6379/0"),
                      ssl_options)


# Now consume:
seconds_to_consume = 10.0
heartbeat = 60
serializer = "application/json"
queue = "reporting.accounts"
sub.consume(callback=handle_message,
            queue=queue,
            exchange=None,
            routing_key=None,
            serializer=serializer,
            heartbeat=heartbeat,
            time_to_wait=seconds_to_consume)

log.info("End - {}".format(name))
