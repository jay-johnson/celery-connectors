import logging
import time
from kombu import Connection, Queue, Exchange
from kombu.common import maybe_declare
from kombu.mixins import ConsumerProducerMixin
from kombu.pools import producers
from celery_connectors.utils import SUCCESS
from celery_connectors.utils import FAILED
from celery_connectors.utils import ERROR
from celery_connectors.utils import ev
from celery_connectors.utils import build_sample_msgs
from celery_connectors.utils import calc_backoff_timer
from celery_connectors.build_ssl_options import build_ssl_options
from celery_connectors.log.setup_logging import setup_logging


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

setup_logging()
name = ev("APP_NAME", "robopubsub")
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


def send_task_msg(conn=None,
                  data={},
                  exchange=None,     # kombu.Exchange object
                  routing_key=None,  # string
                  priority="high",
                  priority_routing={},
                  serializer="json",
                  **kwargs):

    res = {"status": ERROR,  # non-zero is failure
           "error": ""}

    use_routing_key = routing_key
    if not use_routing_key:
        if priority in priority_routing:
            use_routing_key = priority_routing[priority]
    # end of finding the routing key

    payload = data
    if len(payload) == 0:
        res["status"] = ERROR
        res["error"] = "Please set a data argument to a dict " + \
                       "to publish messages"
        return res

    if not conn:
        res["status"] = ERROR
        res["error"] = "Please set a valid connection (conn) " + \
                       "to publish messages"
        return res

    if not exchange:
        res["status"] = ERROR
        res["error"] = "Please set an exchange to publish"
        return res

    if not use_routing_key:
        res["status"] = ERROR
        res["error"] = "Please set pass in a routing_key " + \
                       "or a valid priority_routing with an" + \
                       "entry to a routing_key string to " + \
                       "send a task message"
        return res

    log.info(("{} publish - "
              "ex={} rk={} sz={}")
             .format(name,
                     exchange,
                     use_routing_key,
                     serializer))

    last_step = "try"
    try:
        with producers[conn].acquire(block=True) as producer:

            # if you throw here, please pass in a kombu.Exchange
            # because the type of Exchange should not be handled in
            # the send method
            last_step = "Please set an exchange to publish"
            last_step = "maybe declare={}".format(exchange.name)
            maybe_declare(exchange,
                          producer.channel)

            last_step = "publish rk={}".format(routing_key)
            producer.publish(payload,
                             serializer=serializer,
                             exchange=exchange,
                             routing_key=routing_key)

        res["status"] = SUCCESS
        res["error"] = ""

    except Exception as e:
        res["status"] = FAILED
        res["error"] = ("{} producer threw "
                        "exception={} ex={} rk={} "
                        "last_step={}").format(
                            name,
                            e,
                            exchange,
                            routing_key,
                            last_step)

        log.error(("{} producer threw "
                   "exception={} ex={} rk={} "
                   "last_step={}")
                  .format(name,
                          e,
                          exchange,
                          routing_key,
                          last_step))
    # end of try to send

    return res
# end of send_task_msg


def run_publisher(broker_url,
                  exchange=None,     # kombu.Exchange object
                  routing_key=None,  # string
                  msgs=[],
                  num_per_batch=-1,
                  priority="high",
                  serializer="json",
                  ssl_options={},
                  transport_options={},
                  *args,
                  **kwargs):

    log.info("connecting")

    with Connection(broker_url,
                    ssl=ssl_options,
                    transport_options=transport_options) as conn:

        num_to_send = len(msgs)

        if num_to_send == 0:
            log.info(("no msgs={} to publish")
                     .format(num_to_send))
            return

        log.info(("publishing ex={} rk={} "
                  "msgs={}")
                 .format(exchange,
                         routing_key,
                         num_to_send))

        num_sent = 0
        not_done = True
        num_fails = 0

        while not_done:

            cur_msg = msgs[num_sent]

            send_res = send_task_msg(conn=conn,
                                     data=cur_msg,
                                     exchange=exchange,
                                     routing_key=routing_key,
                                     priority=priority,
                                     priority_routing=priority_routing,
                                     serializer=serializer)

            if send_res["status"] == SUCCESS:
                num_fails = 0
                num_sent += 1
                if num_sent >= num_to_send:
                    not_done = False
            else:
                num_fails += 1
                sleep_duration = calc_backoff_timer(num_fails)
                log.info(("publish failed - {} - exch={} rk={}"
                          "sleep={} seconds retry={}")
                         .format(send_res["error"],
                                 exchange,
                                 routing_key,
                                 sleep_duration,
                                 num_fails))

                if num_fails > 100000:
                    num_fails = 1

                time.sleep(sleep_duration)
            # end of if done

        # end of sending all messages

    # end of with kombu.Connection

# end of run_publisher


class WorkerProducerConsumerMixin(ConsumerProducerMixin):

    def __init__(self,
                 conn=None,
                 callback=None,
                 task_queues=[],
                 prefetch_count=1):

        self.name = "pubsub-mix"
        self.connection = conn
        self.task_queues = task_queues
        self.prefetch_count = prefetch_count
        self.use_callback = self.handle_message

        if callback:
            self.use_callback = callback
    # end of __init__

    def set_callback(self, callback):
        self.use_callback = callback
    # end of set_task_queues

    def set_task_queues(self, task_queues=[]):
        self.task_queues = task_queues
    # end of set_task_queues

    def get_consumers(self, Consumer, channel):  # noqa F811

        if len(self.task_queues) == 0:
            log.error(("There are no task_queues={} "
                       "to consume")
                      .format(len(self.task_queues)))
            return []

        return [Consumer(queues=self.task_queues,
                         prefetch_count=self.prefetch_count,
                         callbacks=[self.use_callback])]
    # end of get_consumers

    def handle_message(self, body, message):
        log.info(("default handle_message - "
                  "acking - msg={}")
                 .format(body))
        message.ack()
    # end of handle_message

# end of WorkerProducerConsumerMixin


def run_consumer(broker_url,
                 ssl_options={},
                 transport_options={},
                 task_queues=[],
                 callback=None,
                 prefetch_count=1,
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

            WorkerProducerConsumerMixin(
                    conn=conn,
                    task_queues=task_queues,
                    callback=callback,
                    prefetch_count=prefetch_count).run()
        except KeyboardInterrupt:
            log.info("Received Interrupt - Shutting down")
    # end of with kombu.Connection

# end of run_consumer


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
              priority="high")

log.info("Done Publishing")

log.info(("Consuming queues={}")
         .format(len(task_queues)))

run_consumer(broker_url=broker_url,
             ssl_options=ssl_options,
             transport_options=transport_options,
             task_queues=task_queues,
             prefetch_count=prefetch_count)

log.info("Done")
