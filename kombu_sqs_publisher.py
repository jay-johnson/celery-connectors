#!/usr/bin/env python

import logging
import datetime
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.publisher import Publisher

setup_logging()

name = "kombu-sqs-publisher"

log = logging.getLogger(name)

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

sqs_auth_url = ev("BROKER_URL",
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
queue = "test1"
exchange = "test1"
routing_key = "test1"
max_timeout = 43200
transport_options = {}

if not pub:
    log.error("Failed to connect to broker={}".format(auth_url))
else:

    log.info("Building message")

    # Now send:
    body = {"account_id": 111,
            "subscription_id": 222,
            "stripe_id": 333,
            "sent": datetime.datetime.now().isoformat(),
            "product_id": "DEF"}

    log.info("Sending user conversion event msg={} ex={} rk={}".format(body,
                                                                       exchange,
                                                                       routing_key))

    send_result = pub.publish(
        body=body,
        exchange=exchange,
        routing_key=routing_key,
        queue=queue,
        serializer=serializer,
        retry=True,
        transport_options=transport_options)

    log.info("End - {}".format(name))
# end of valid or not
