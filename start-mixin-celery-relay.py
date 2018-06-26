#!/usr/bin/env python

from kombu import Exchange, Queue
from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.build_ssl_options import build_ssl_options
from celery_connectors.run_jtoc_relay import run_jtoc_relay


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

name = ev("APP_NAME", "jtoc_relay")
log = build_colorized_logger(
    name=name)


broker_url = ev("SUB_BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
exchange_name = ev("CONSUME_EXCHANGE", "ecomm.api")
exchange_type = ev("CONSUME_EXCHANGE_TYPE", "topic")
routing_key = ev("CONSUME_ROUTING_KEY", "ecomm.api.west")
queue_name = ev("CONSUME_QUEUE", "ecomm.api.west")
prefetch_count = int(float(ev("PREFETCH_COUNT", "1")))
priority_routing = {"high": queue_name,
                    "low": queue_name}
use_exchange = Exchange(exchange_name, type=exchange_type)
use_queue = Queue(queue_name, exchange=use_exchange, routing_key=routing_key)
task_queues = [
    use_queue
]
ssl_options = build_ssl_options()

relay_broker_url = ev("RELAY_BROKER_URL", "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
relay_backend_url = ev("RELAY_BACKEND_URL", "redis://localhost:6379/10")
relay_exchange_name = ev("RELAY_EXCHANGE", "")
relay_exchange_type = ev("RELAY_EXCHANGE_TYPE", "direct")
relay_routing_key = ev("RELAY_ROUTING_KEY", "reporting.payments")
relay_exchange = Exchange(relay_exchange_name, type=relay_exchange_type)

transport_options = {}

log.info(("Consuming queues={}")
         .format(len(task_queues)))

run_jtoc_relay(broker_url=broker_url,
               ssl_options=ssl_options,
               transport_options=transport_options,
               task_queues=task_queues,
               prefetch_count=prefetch_count,
               relay_broker_url=relay_broker_url,
               relay_backend_url=relay_backend_url,
               relay_exchange=relay_exchange,
               relay_exchange_type=relay_exchange_type,
               relay_routing_key=relay_routing_key)

log.info("Done")
