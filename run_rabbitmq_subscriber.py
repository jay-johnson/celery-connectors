#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import logging
from celery import Celery
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.subscriber import Subscriber

setup_logging()

name = "run-rabbitmq-subscriber"

log = logging.getLogger(name)

log.info("Start - {}".format(name))


recv_msgs = []


def handle_message(body, message):
    log.info("recv msg props={} body={}".format(message, body))
    recv_msgs.append(body)
    message.ack()
# end of handle_message


# Initialize Celery application
ssl_options = {}
app = Celery()
sub = Subscriber("rabbitmq-subscriber",
                 ev("BROKER_URL", "amqp://rabbitmq:rabbitmq@localhost:5672//"),
                 app,
                 ssl_options)


# Now consume:
exchange = "reporting"
routing_key = "reporting.accounts"
queue = "reporting.accounts"
sub.consume(callback=handle_message,
            queue=queue,
            exchange=exchange,
            routing_key=routing_key)

log.info("End - {}".format(name))
