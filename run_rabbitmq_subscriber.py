#!/usr/bin/env python

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
    log.info(("callback received msg "
              "body={}")
             .format(body))
    recv_msgs.append(body)
    message.ack()
# end of handle_message


# Initialize Celery application
ssl_options = {}
transport_options = {}
conn_attrs = {"task_default_queue": "celery.rabbit.sub",
              "task_default_exchange": "celery.rabbit.sub"}
app = Celery()
sub = Subscriber(name="rabbitmq-subscriber",
                 auth_url=ev("BROKER_URL",
                             "amqp://rabbitmq:rabbitmq@localhost:5672//"),
                 app=app,
                 transport_options=transport_options,
                 ssl_options=ssl_options,
                 **conn_attrs)


# Now consume:
exchange = "reporting"
routing_key = "reporting.accounts"
queue = "reporting.accounts"
sub.consume(callback=handle_message,
            queue=queue,
            exchange=exchange,
            routing_key=routing_key)

log.info("End - {}".format(name))
