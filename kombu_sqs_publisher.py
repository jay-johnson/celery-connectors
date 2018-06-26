#!/usr/bin/env python

import datetime
from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.publisher import Publisher


name = "kombu-sqs-publisher"
log = build_colorized_logger(
    name=name)

log.info("Start - {}".format(name))


# Initialize Publisher
# http://docs.celeryproject.org/en/latest/getting-started/brokers/sqs.html
# https://github.com/celery/kombu/blob/master/kombu/transport/SQS.py
aws_key = ev(
            "SQS_AWS_ACCESS_KEY",
            "not_a_key")
aws_secret = ev(
            "SQS_AWS_SECRET_KEY",
            "not_a_secret")

sqs_auth_url = ev("SUB_BROKER_URL",
                  "sqs://{}:{}@".format(
                      aws_key,
                      aws_secret))

ssl_options = {}
pub = Publisher("kombu-sqs-publisher",
                sqs_auth_url,
                ssl_options)
# sample: "sqs://ABCDEFGHIJKLMNOPQRST:ZYXK7NiynGlTogH8Nj+P9nlE73sq3@"
# ^ from the doc: 'you must remember to include the "@" at the end.'


# Now consume:
seconds_to_consume = 10.0
serializer = "json"
exchange = ev("CONSUME_EXCHANGE", "test1")
routing_key = ev("CONSUME_ROUTING_KEY", "test1")
queue = ev("CONSUME_QUEUE", "test1")
max_timeout = 43200
transport_options = {}

if not pub:
    log.error(("Failed to connect to "
               "broker={}")
              .format(sqs_auth_url))
else:

    # Create the message:
    now = datetime.datetime.now().isoformat()
    body = {"account_id": 111,
            "subscription_id": 222,
            "stripe_id": 333,
            "created": now,
            "product_id": "DEF"}

    log.info(("Sending user conversion event "
              "msg={} ex={} rk={}")
             .format(body,
                     exchange,
                     routing_key))

    # Publish the message:
    msg_sent = pub.publish(
        body=body,
        exchange=exchange,
        routing_key=routing_key,
        queue=queue,
        serializer=serializer,
        retry=True,
        transport_options=transport_options)

    log.info(("End - {} sent={}")
             .format(name,
                     msg_sent))
# end of valid publisher or not
