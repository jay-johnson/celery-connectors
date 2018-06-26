#!/usr/bin/env python

from kombu import Exchange, Queue
from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.utils import build_sample_msgs
from celery_connectors.build_ssl_options import build_ssl_options
from celery_connectors.run_publisher import run_publisher


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

name = ev("APP_NAME", "robopub")
log = build_colorized_logger(
    name=name)


broker_url = ev("PUB_BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
exchange_name = ev("PUBLISH_EXCHANGE", "ecomm.api")
exchange_type = ev("PUBLISH_EXCHANGE_TYPE", "topic")
routing_key = ev("PUBLISH_ROUTING_KEY", "ecomm.api.west")
queue_name = ev("PUBLISH_QUEUE", "ecomm.api.west")
priority_routing = {"high": queue_name,
                    "low": queue_name}
use_exchange = Exchange(exchange_name, type=exchange_type)
use_routing_key = routing_key
use_queue = Queue(queue_name, exchange=use_exchange, routing_key=routing_key)
task_queues = [
    use_queue
]
ssl_options = build_ssl_options()
transport_options = {}

num_msgs_to_send = int(float(ev("NUM_MSG_TO_PUBLISH", "20000")))
log.info(("Generating messages={}")
         .format(num_msgs_to_send))

# relay_task_lag = 0.0
# worker_task_lag = 0.0
# processing_lag_data = {"relay_simulate_processing_lag": worker_task_lag,
#                       "simulate_processing_lag": worker_task_lag}
# msgs = build_sample_msgs(num=num_msgs_to_send,
#                          data=processing_lag_data)

msgs = build_sample_msgs(num=num_msgs_to_send,
                         data={})

log.info(("Publishing messages={}")
         .format(len(msgs)))

run_publisher(broker_url=broker_url,
              exchange=use_exchange,        # kombu.Exchange object
              routing_key=use_routing_key,  # string
              msgs=msgs,
              ssl_options=ssl_options,
              transport_options=transport_options,
              priority="high",
              priority_routing=priority_routing,
              silent=True,
              publish_silent=True)

log.info("Done Publishing")
