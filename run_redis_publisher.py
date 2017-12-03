#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import logging
from kombu import Connection, Queue, Exchange, Producer
from celery_connectors.utils import ev
from celery_connectors.logging.setup_logging import setup_logging

setup_logging()

name = "run-redis-publisher"

log = logging.getLogger(name)

log.info("Start - {}".format(name))

# Celery Transports:
# http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html#transport-comparison

ex_name = ev("EXCHANGE", "reporting.accounts")
queue_name = ev("QUEUE", "reporting.accounts")
routing_key = ev("RK", "reporting.accounts")

ex = Exchange(ex_name, type="direct")
queue = Queue(queue_name, exchange=ex, routing_key=routing_key)

declare_entities = [
    ex,
    queue
]

auth_url = ev("BROKER_URL", "redis://localhost:6379/0")
serializer = "json"
app = None

# https://redis.io/topics/security
#
# Redis does not support encryption, but I would like to try out ssl-termination
# using an haproxy/nginx container running as an ssl-proxy to see if this works.

# import ssl
# Connection("amqp://", login_method='EXTERNAL', ssl={
#               "ca_certs": '/etc/pki/tls/certs/something.crt',
#               "keyfile": '/etc/something/system.key',
#               "certfile": '/etc/something/system.cert',
#               "cert_reqs": ssl.CERT_REQUIRED,
#          })
#
conn = Connection(auth_url)
channel = conn.channel()
app = Producer(channel=channel,
               exchange=ex,
               routing_key=routing_key,
               serializer=serializer,
               on_return=None)

queue.maybe_bind(conn)
queue.declare()


if not app:
    log.error("Failed to connect to broker={}".format(auth_url))
else:

    log.info("Building message")

    # Now send:
    msg = {"account_id": 123}

    log.info("Sending msg={} ex={} rk={}".format(msg, ex, routing_key))

    send_result = app.publish(
        body=msg,
        routing_key=routing_key,
        serializer=serializer,
        exchange=ex.name,
        retry=True
    )

    log.info("End - {}".format(name))
# end of valid or not
