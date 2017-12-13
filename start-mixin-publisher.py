#!/usr/bin/env python

import logging
from kombu import Exchange, Queue
from celery_connectors.utils import ev
from celery_connectors.utils import build_sample_msgs
from celery_connectors.build_ssl_options import build_ssl_options
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.run_publisher import run_publisher


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

setup_logging()
name = ev("APP_NAME", "robopub")
log = logging.getLogger(name)


broker_url = ev("BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
exchange_name = ev("EXCHANGE_NAME", "ecomm.api")
exchange_type = ev("EXCHANGE_TYPE", "topic")
routing_key = ev("ROUTING_KEY", "ecomm.api.west")
queue_name = ev("QUEUE_NAME", "ecomm.api.west")
prefetch_count = int(ev("PREFETCH_COUNT", "1"))
priority_routing = {"high": "ecomm.api.west",
                    "low": "ecomm.api.east"}
use_exchange = Exchange(exchange_name, type=exchange_type)
use_routing_key = routing_key
use_queue = Queue(queue_name, exchange=use_exchange, routing_key=routing_key)
task_queues = [
    use_queue
]
ssl_options = build_ssl_options()
transport_options = {}

num_msgs_to_send = 10
log.info(("Generating messages={}")
         .format(num_msgs_to_send))

msgs = build_sample_msgs(num=num_msgs_to_send,
                         data={"simulated_lag": 1.0})

log.info(("Publishing messages={}")
         .format(len(msgs)))

run_publisher(broker_url=broker_url,
              exchange=use_exchange,        # kombu.Exchange object
              routing_key=use_routing_key,  # string
              msgs=msgs,
              ssl_options=ssl_options,
              transport_options=transport_options,
              priority="high",
              priority_routing=priority_routing)

log.info("Done Publishing")
