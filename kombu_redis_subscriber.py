#!/usr/bin/env python

from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.kombu_subscriber import KombuSubscriber


name = "kombu-redis-subscriber"
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
ssl_options = {}
sub = KombuSubscriber("kombu-redis-subscriber",
                      ev("SUB_BROKER_URL",
                         "redis://localhost:6379/0"),
                      ssl_options)


# Now consume:
seconds_to_consume = 10.0
heartbeat = 60
serializer = "application/json"
queue = ev("CONSUME_QUEUE", "reporting.accounts")
sub.consume(callback=handle_message,
            queue=queue,
            exchange=None,
            routing_key=None,
            serializer=serializer,
            heartbeat=heartbeat,
            time_to_wait=seconds_to_consume)

log.info("End - {}".format(name))
