#!/usr/bin/env python

from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.message_processor import MessageProcessor


name = "msg-proc"
log = build_colorized_logger(
    name=name)

log.info("Start - {}".format(name))

# want to change where you're subscribing vs publishing?
sub_ssl_options = {}
sub_auth_url = ev("SUB_BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
pub_ssl_options = {}
pub_auth_url = ev("PUB_BROKER_URL", "redis://localhost:6379/0")

# start the message processor
msg_proc = MessageProcessor(name=name,
                            sub_auth_url=sub_auth_url,
                            sub_ssl_options=sub_ssl_options,
                            pub_auth_url=pub_auth_url,
                            pub_ssl_options=pub_ssl_options)

# configure where this is consuming:
queue = ev("CONSUME_QUEUE", "user.events.conversions")

# Relay Publish Hook - sending to Redis
# where is it sending handled messages using a publish-hook or auto-caching:
exchange = ev("PUBLISH_EXCHANGE", "reporting.accounts")
routing_key = ev("PUBLISH_ROUTING_KEY", "reporting.accounts")

# set up the controls and long-term connection attributes
seconds_to_consume = 10.0
heartbeat = 60
serializer = "application/json"
pub_serializer = "json"
expiration = None
consume_forever = True

# start consuming
msg_proc.consume_queue(queue=queue,
                       heartbeat=heartbeat,
                       expiration=expiration,
                       sub_serializer=serializer,
                       pub_serializer=pub_serializer,
                       seconds_to_consume=seconds_to_consume,
                       forever=consume_forever,
                       # Optional: if you're chaining a publish hook to another system
                       exchange=exchange,
                       # Optional: if you're chaining a publish hook to another system
                       routing_key=routing_key)

log.info("End - {}".format(name))
