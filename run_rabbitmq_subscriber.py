#!/usr/bin/env python

import logging
from celery import Celery
from celery_connectors.utils import ev
from celery_connectors.utils import get_source_info_from_msg
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.subscriber import Subscriber

setup_logging()

name = "run-rabbitmq-subscriber"

log = logging.getLogger(name)

log.info("Start - {}".format(name))


recv_msgs = []


def handle_message(body, message):
    source_info = get_source_info_from_msg(message)
    log.info(("callback received msg "
              "body={} from_ex={} from_rk={}")
             .format(body,
                     source_info["src_exchange"],
                     source_info["src_routing_key"]))
    recv_msgs.append(body)
    message.ack()
# end of handle_message


# Initialize Celery application
ssl_options = {}

# http://docs.celeryproject.org/en/latest/userguide/calling.html#calling-retry
# allow publishes to retry for a time
task_publish_retry_policy = {
    "interval_max": 1,
    "max_retries": 120,     # None - forever
    "interval_start": 0.1,
    "interval_step": 0.2}

# Confirm publishes with Celery
# https://github.com/celery/kombu/issues/572
transport_options = {
    "confirm_publish": True}

conn_attrs = {
    "task_default_queue": "celery.rabbit.sub",
    "task_default_exchange": "celery.rabbit.sub",
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-worker_prefetch_multiplier
    "worker_prefetch_multiplier": 1,  # consume 1 message at a time
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-worker_prefetch_multiplier
    "prefetch_count": 3,  # consume 1 message at a time per worker (3 workers)
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_heartbeat
    "broker_heartbeat": 240,  # in seconds
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_connection_max_retries
    "broker_connection_max_retries": None,  # None is forever
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_acks_late
    "task_acks_late": True,  # on consume do not send an immediate ack back
    "task_publish_retry_policy": task_publish_retry_policy}

app = Celery()
sub = Subscriber(name="rabbitmq-subscriber",
                 auth_url=ev("SUB_BROKER_URL",
                             "pyamqp://rabbitmq:rabbitmq@localhost:5672//"),
                 app=app,
                 transport_options=transport_options,
                 ssl_options=ssl_options,
                 **conn_attrs)


# Now consume:
queues = [
    ev("CONSUME_QUEUE", "reporting.accounts"),
    ev("CONSUME_QUEUE2", "reporting.subscriptions")
]
sub.consume(callback=handle_message,
            queues=queues,
            prefetch_count=conn_attrs["prefetch_count"])

log.info("End - {}".format(name))
