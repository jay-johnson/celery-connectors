import logging
from kombu.mixins import ConsumerProducerMixin
from celery_connectors.utils import ev
from celery_connectors.utils import build_msg
from celery_connectors.run_publisher import run_publisher


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

name = ev("APP_NAME", "relay-wrk")
log = logging.getLogger(name)


class RelayWorker(ConsumerProducerMixin):

    def __init__(self,
                 name="relay",
                 conn=None,
                 callback=None,
                 task_queues=[],
                 prefetch_count=1,
                 relay_exchange=None,
                 relay_routing_key=None,
                 relay_broker_url=None,
                 relay_ssl_options={},
                 relay_transport_options={},
                 relay_serializer="json",
                 on_exception_should_ack=False,
                 on_exception_should_reject=False,
                 on_exception_should_requeue=True,
                 on_relay_ex_should_ack=False,
                 on_relay_ex_should_reject=False,
                 on_relay_ex_should_requeue=True):

        self.name = name
        self.connection = conn
        self.task_queues = task_queues
        self.prefetch_count = prefetch_count
        self.use_callback = self.handle_message

        self.relay_broker_url = relay_broker_url
        self.relay_ssl_options = relay_ssl_options
        self.relay_transport_options = relay_transport_options
        self.relay_exchange = relay_exchange
        self.relay_routing_key = relay_routing_key
        self.relay_serializer = relay_serializer

        self.on_exception_should_ack = on_exception_should_ack
        self.on_exception_should_reject = on_exception_should_reject
        self.on_exception_should_requeue = on_exception_should_requeue

        self.on_relay_ex_should_ack = on_relay_ex_should_ack
        self.on_relay_ex_should_reject = on_relay_ex_should_reject
        self.on_relay_ex_should_requeue = on_relay_ex_should_requeue

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
        else:
            log.info(("creating consumer for "
                      "queues={} callback={} "
                      "relay_ex={} relay_rk={} "
                      "prefetch={}")
                     .format(len(self.task_queues),
                             str(self.use_callback.__name__),
                             self.relay_exchange,
                             self.relay_routing_key,
                             self.prefetch_count))

        return [Consumer(queues=self.task_queues,
                         prefetch_count=self.prefetch_count,
                         auto_declare=True,
                         callbacks=[self.use_callback])]
    # end of get_consumers

    def send_response_to_broker(
                self,
                handler_success,
                relay_success,
                relay_ran,
                should_ack,
                should_reject,
                should_requeue,
                message):

        """
        Allow derived classes to override how
        default exceptions and relay errors
        can be ack-ed, reject-ed or requeue-ed
        based off the worker's initial values
        """

        if handler_success and relay_success:
            log.debug("hs-rs success")
            self.handle_response(
                should_ack=should_ack,
                should_reject=should_reject,
                should_requeue=should_requeue,
                message=message)
        else:
            # handle general exceptions first
            if not handler_success:
                log.debug("handler failed")
                self.handle_response(
                    shold_ack=self.on_exception_should_ack,
                    should_reject=self.on_exception_should_reject,
                    should_requeue=self.on_exception_should_requeue,
                    message=message)
            elif not relay_success:
                log.debug("relay failed")
                self.handle_response(
                    shold_ack=self.on_relay_ex_should_ack,
                    should_reject=self.on_relay_ex_should_reject,
                    should_requeue=self.on_relay_ex_should_requeue,
                    message=message)
            else:
                log.debug("general failure")
                self.handle_response(
                    shold_ack=self.on_exception_should_ack,
                    should_reject=self.on_exception_should_reject,
                    should_requeue=self.on_exception_should_requeue,
                    message=message)
        # end of if success or handle possible failures

    # end of send_response_to_broker

    def handle_response(self,
                        should_ack=True,
                        should_reject=False,
                        should_requeue=False,
                        message=None):

        if not message:
            log.error(("No Message to Handle - Please check the derived "
                       "'handle_response' to make sure there is no "
                       "message loss"))
            return

        if should_ack:
            log.debug("ack - start")
            message.ack()
            log.debug("ack - end")
        else:
            if should_requeue:
                log.debug("requeue - start")
                message.requeue()
                log.debug("requeue - end")
            else:
                log.debug("reject - start")
                message.reject()
                log.debug("reject - end")
        # end of cascade in case multiples are
        # passed in with True by accident

    # end of handle_response

    def handle_relay(self,
                     body={},
                     message={},
                     relay_exchange=None,
                     relay_routing_key=None,
                     serializer="json"):

        """
        Allow derived classes to customize
        how they 'handle_relay'
        """

        if not relay_exchange and not relay_routing_key:
            log.error(("Relay misconfigured: please set either a "
                       "relay_exchange={} or a relay_routing_key={}")
                      .format(relay_exchange,
                              relay_routing_key))
            return False

        try:
            base_relay_payload = {"org_msg": body,
                                  "relay_name": self.name}

            log.debug("build relay_payload")
            relay_payload = build_msg(base_relay_payload)

            log.info(("send start - relay_ex={} relay_rk={} id={}")
                     .format(relay_exchange,
                             relay_routing_key,
                             relay_payload["msg_id"]))

            run_publisher(broker_url=self.relay_broker_url,
                          exchange=relay_exchange,
                          routing_key=relay_routing_key,
                          ssl_options=self.relay_ssl_options,
                          transport_options=self.relay_transport_options,
                          serializer=self.relay_serializer,
                          msgs=[relay_payload])

            log.info(("send done - id={}")
                     .format(relay_payload["msg_id"]))

        except Exception as e:
            log.error(("Relay failed: with ex={} when sending to "
                       "relay_exchange={} relay_routing_key={}")
                      .format(e,
                              relay_exchange,
                              relay_routing_key))
            return False
        # end of try/ex

        return True
    # end of handle_relay

    def handle_message(self, body, message):

        should_ack = True
        should_reject = False
        should_requeue = False

        handler_success = False

        relay_ran = False
        relay_success = False

        try:
            log.info(("default handle_message - "
                      "acking - msg={}")
                     .format(body))

            handler_success = True
            should_ack = True

            if self.relay_exchange or self.relay_routing_key:
                relay_success = self.handle_relay(
                                    body=body,
                                    message=message,
                                    relay_exchange=self.relay_exchange,
                                    relay_routing_key=self.relay_routing_key,
                                    serializer=self.relay_serializer)
                relay_ran = True
            else:
                relay_success = True

        except Exception as e:
            handler_success = False
            log.error(("Failed RelayWorker.handle_message "
                       "with ex={}")
                      .format(e))
        # end of try/ex

        #
        # Note: if derived by another class:
        #
        # this MUST ack/requeue/reject a message to
        # allow processing to continue correctly
        self.send_response_to_broker(
                handler_success=handler_success,
                relay_success=relay_success,
                relay_ran=relay_ran,
                should_ack=should_ack,
                should_reject=should_reject,
                should_requeue=should_requeue,
                message=message)

    # end of handle_message

# end of RelayWorker
