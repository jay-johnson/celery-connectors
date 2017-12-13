import logging
from kombu import Connection
from celery_connectors.utils import ev
from celery_connectors.relay_worker import RelayWorker


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

name = ev("APP_NAME", "relay")
log = logging.getLogger(name)


def run_consumer_relay(broker_url,
                       ssl_options={},
                       transport_options={},
                       task_queues=[],
                       callback=None,
                       prefetch_count=1,
                       relay_broker_url=None,
                       relay_exchange=None,
                       relay_routing_key=None,
                       *args,
                       **kwargs):

    if len(broker_url) == 0:
        log.error(("Please pass in a valid broker_url "
                   "to consume"))
        return

    if len(task_queues) == 0:
        log.error(("Please pass in a list of task_queues to "
                   "consume"))
        return

    with Connection(broker_url,
                    ssl=ssl_options,
                    transport_options=transport_options) as conn:
        try:
            log.info(("consuming queues={}")
                     .format(task_queues))

            RelayWorker(
                    "json-to-json-relay",
                    conn=conn,
                    task_queues=task_queues,
                    callback=callback,
                    prefetch_count=prefetch_count,
                    relay_broker_url=relay_broker_url,
                    relay_exchange=relay_exchange,
                    relay_routing_key=relay_routing_key,
                    **kwargs).run()

        except KeyboardInterrupt:
            log.info("Received Interrupt - Shutting down")
    # end of with kombu.Connection

# end of run_consumer_relay
