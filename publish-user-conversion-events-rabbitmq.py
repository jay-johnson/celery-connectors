#!/usr/bin/env python

import logging
import datetime
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.publisher import Publisher

setup_logging()

name = "publish-user-conversion-events"

log = logging.getLogger(name)

log.info("Start - {}".format(name))

exchange_name = ev("PUBLISH_EXCHANGE", "user.events")
routing_key = ev("PUBLISH_ROUTING_KEY", "user.events.conversions")
queue_name = ev("PUBLISH_QUEUE", "user.events.conversions")
auth_url = ev("PUB_BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
serializer = "json"

# import ssl
# Connection("amqp://", login_method='EXTERNAL', ssl={
#               "ca_certs": '/etc/pki/tls/certs/something.crt',
#               "keyfile": '/etc/something/system.key',
#               "certfile": '/etc/something/system.cert',
#               "cert_reqs": ssl.CERT_REQUIRED,
#          })
#
ssl_options = {}
app = Publisher("publish-uce-rabbitmq",
                auth_url,
                ssl_options)

if not app:
    log.error("Failed to connect to broker={}".format(auth_url))
else:

    # Create the message:
    now = datetime.datetime.now().isoformat()
    body = {"account_id": 777,
            "subscription_id": 888,
            "stripe_id": 999,
            "product_id": "XYZ",
            "created": now}

    log.info(("Sending user conversion event "
              "msg={} ex={} rk={}")
             .format(body, exchange_name, routing_key))

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
# end of valid or not
