#!/usr/bin/env python

import datetime
from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.publisher import Publisher


name = "run-redis-publisher"
log = build_colorized_logger(
    name=name)

log.info("Start - {}".format(name))

# Celery Transports:
# http://docs.celeryproject.org/projects/kombu/en/latest/userguide/connections.html#transport-comparison

exchange_name = ev("PUBLISH_EXCHANGE", "reporting.accounts")
routing_key = ev("PUBLISH_EXCHANGE", "reporting.accounts")
queue_name = ev("PUBLISH_QUEUE", "reporting.accounts")
auth_url = ev("PUB_BROKER_URL", "redis://localhost:6379/0")
serializer = "json"

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
ssl_options = {}
app = Publisher("redis-publisher",
                auth_url,
                ssl_options)

if not app:
    log.error(("Failed to connect to broker={}")
              .format(auth_url))
else:

    # Now send:
    now = datetime.datetime.now().isoformat()
    body = {"account_id": 123,
            "created": now}

    log.info(("Sending msg={} "
              "ex={} rk={}")
             .format(body,
                     exchange_name,
                     routing_key))

    # Publish the message:
    msg_sent = app.publish(body=body,
                           exchange=exchange_name,
                           routing_key=routing_key,
                           queue=queue_name,
                           serializer=serializer,
                           retry=True)

    log.info(("End - {} sent={}")
             .format(name,
                     msg_sent))
# end of valid publisher or not
