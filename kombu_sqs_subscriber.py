#!/usr/bin/env python

from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.kombu_subscriber import KombuSubscriber


name = "kombu-sqs-subscriber"
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


# Initialize KombuSubscriber
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

transport_options = {}
ssl_options = {}
sub = KombuSubscriber("kombu-sqs-subscriber",
                      sqs_auth_url,
                      ssl_options)
# sample: "sqs://ABCDEFGHIJKLMNOPQRST:ZYXK7NiynGlTogH8Nj+P9nlE73sq3@"
# ^ from the doc: 'you must remember to include the "@" at the end.'


# Now consume:
seconds_to_consume = 10.0
serializer = "application/json"
queue = "test1"
exchange = "test1"
routing_key = "test1"
transport_options = {"polling_interval": 0.3,
                     "visibility_timeout": 600}
sub.consume(callback=handle_message,
            queue=queue,
            exchange=exchange,
            routing_key=routing_key,
            serializer=serializer,
            time_to_wait=seconds_to_consume,
            transport_options=transport_options)

log.info("End - {}".format(name))
