#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import logging
from celery import Celery
from celery_connectors.utils import ev
from celery_connectors.logging.setup_logging import setup_logging
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
app = Celery()
sub = Subscriber("rabbitmq-publisher", ev("BROKER_URL", "amqp://rabbitmq:rabbitmq@localhost:5672//"), app)


# Now send:
msg = {"account_id": 123}
dst_ex_name = "reporting"
routing_key = "reporting.accounts"
dst_queue = "reporting.accounts"
sub.consume(callback=handle_message,
            dst_queue_name=dst_queue,
            dst_ex_name=dst_ex_name,
            routing_key=routing_key)

log.info("End - {}".format(name))
