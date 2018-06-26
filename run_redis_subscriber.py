#!/usr/bin/env python

from spylunking.log.setup_logging import build_colorized_logger
from celery import Celery
from celery_connectors.utils import ev
from celery_connectors.subscriber import Subscriber


name = "run-redis-subscriber"
log = build_colorized_logger(
    name=name)

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
    "task_default_queue": "celery.redis.sub",
    "task_default_exchange": "celery.redis.sub",
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
sub = Subscriber("redis-subscriber",
                 ev("SUB_BROKER_URL", "redis://localhost:6379/0"),
                 app,
                 ssl_options,
                 **conn_attrs)


# Now consume:
queue = ev("CONSUME_QUEUE", "reporting.accounts")
sub.consume(callback=handle_message,
            queue=queue,
            exchange=None,
            routing_key=None,
            prefetch_count=conn_attrs["prefetch_count"])

log.info("End - {}".format(name))
