import logging
import time
from kombu.mixins import ConsumerProducerMixin
from celery_connectors.utils import ev
from celery_connectors.utils import build_msg
from celery_connectors.utils import get_exchange_from_msg
from celery_connectors.utils import get_routing_key_from_msg
from celery_connectors.run_publisher import run_publisher


# Credits and inspirations from these great sources:
#
# https://github.com/celery/kombu/blob/master/examples/rpc-tut6/rpc_server.py
# https://gist.github.com/oubiwann/3843016
# https://gist.github.com/eavictor/ee7856581619ac60643b57987b7ed580#file-mq_kombu_rpc_server-py
# https://github.com/Skablam/kombu-examples
# https://gist.github.com/mlavin/6671079

log = logging.getLogger(ev("APP_NAME", "relay"))


class RelayWorker(ConsumerProducerMixin):

    def __init__(self,
                 name="relay",
                 conn=None,
                 callback=None,
                 task_queues=[],
                 prefetch_count=1,
                 relay_exchange=None,
                 relay_exchange_type=None,
                 relay_routing_key=None,
                 relay_queue=None,
                 relay_broker_url=None,
                 relay_ssl_options={},
                 relay_transport_options={},
                 relay_serializer="json",
                 relay_handler=None,
                 on_exception_should_ack=False,
                 on_exception_should_reject=False,
                 on_exception_should_requeue=True,
                 on_relay_ex_should_ack=False,
                 on_relay_ex_should_reject=False,
                 on_relay_ex_should_requeue=True,
                 silent=True,
                 publish_silent=False):

        self.name = name
        self.relay_name = "{}-pub".format(self.name)
        self.connection = conn
        self.task_queues = task_queues
        self.prefetch_count = prefetch_count
        self.use_callback = self.handle_message
        self.use_relay_handler = self.handle_relay

        self.relay_broker_url = relay_broker_url
        self.relay_ssl_options = relay_ssl_options
        self.relay_transport_options = relay_transport_options
        self.relay_exchange = relay_exchange
        self.relay_exchange_type = relay_exchange_type
        self.relay_routing_key = relay_routing_key
        self.relay_queue = relay_queue
        self.relay_serializer = relay_serializer

        self.on_exception_should_ack = on_exception_should_ack
        self.on_exception_should_reject = on_exception_should_reject
        self.on_exception_should_requeue = on_exception_should_requeue

        self.on_relay_ex_should_ack = on_relay_ex_should_ack
        self.on_relay_ex_should_reject = on_relay_ex_should_reject
        self.on_relay_ex_should_requeue = on_relay_ex_should_requeue

        self.verbose = not silent
        self.publish_silent = publish_silent

        if callback:
            self.use_callback = callback
        if relay_handler:
            self.use_relay_handler = relay_handler
    # end of __init__

    def set_callback(self, callback):
        self.use_callback = callback
    # end of set_callback

    def set_relay_handler(self, handler_method):
        self.use_relay_handler = handler_method
    # end of set_relay_handler

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

        # http://docs.celeryproject.org/projects/kombu/en/latest/userguide/consumers.html
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

            if self.verbose:
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
                    should_ack=self.on_exception_should_ack,
                    should_reject=self.on_exception_should_reject,
                    should_requeue=self.on_exception_should_requeue,
                    message=message)
            elif not relay_success:
                log.debug("relay failed")
                self.handle_response(
                    should_ack=self.on_relay_ex_should_ack,
                    should_reject=self.on_relay_ex_should_reject,
                    should_requeue=self.on_relay_ex_should_requeue,
                    message=message)
            else:
                log.debug("general failure")
                self.handle_response(
                    should_ack=self.on_exception_should_ack,
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

            if self.verbose:
                log.debug("ack - start")

            message.ack()

            if self.verbose:
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
                     serializer="json",
                     src_exchange=None,
                     src_routing_key=None):

        """
        Allow derived classes to customize
        how they 'handle_relay'
        """

        last_step = "validating"

        if not relay_exchange and not relay_routing_key:
            log.error(("Relay is misconfigured: please set either a "
                       "relay_exchange={} or a relay_routing_key={}")
                      .format(relay_exchange,
                              relay_routing_key))
            return False

        try:

            last_step = "setting up base relay payload"

            base_relay_payload = {"org_msg": body,
                                  "relay_name": self.name}

            if self.verbose:
                log.debug("build relay_payload")

            last_step = "building relay payload"
            relay_payload = build_msg(base_relay_payload)

            source_info = {"relay": self.name,
                           "src_exchange": src_exchange,
                           "src_routing_key": src_routing_key}

            relay_payload["source_info"] = source_info

            use_msg_id = ""
            if "msg_id" in body:
                use_msg_id = body["msg_id"]
            else:
                use_msg_id = relay_payload["msg_id"]

            task_name = ""
            if "task_name" in body:
                task_name = body["task_name"]

            if self.verbose:
                log.info(("relay ex={} rk={} id={}")
                         .format(relay_exchange,
                                 relay_routing_key,
                                 use_msg_id))

            run_publisher(broker_url=self.relay_broker_url,
                          msgs=[relay_payload],
                          exchange=relay_exchange,
                          routing_key=relay_routing_key,
                          ssl_options=self.relay_ssl_options,
                          transport_options=self.relay_transport_options,
                          serializer=self.relay_serializer,
                          silent=not self.verbose,
                          publish_silent=self.publish_silent,
                          log_label=self.relay_name)

            if "relay_simulate_processing_lag" in body["data"]:
                relay_sleep_duration = \
                    body["data"]["relay_simulate_processing_lag"]
                log.info(("task - {} - simulating processing lag "
                          "sleep={} seconds")
                         .format(task_name,
                                 relay_sleep_duration))
                time.sleep(float(relay_sleep_duration))
            # end of handling adding artifical lag for testing Celery

            if self.verbose:
                if "msg_id" in body:
                    log.info(("relay done - "
                              "msg_id={} r_id={}")
                             .format(use_msg_id,
                                     relay_payload["msg_id"]))
                else:
                    log.info(("relay done - "
                              "msg_id={} r_id={}"
                              "body={}")
                             .format(use_msg_id,
                                     relay_payload["msg_id"],
                                     str(body)[0:30]))

            # end of logging
        except Exception as e:
            log.error(("Task Relay failed: with ex={} when sending "
                       "to relay_exchange={} relay_routing_key={} "
                       "last_step={}")
                      .format(e,
                              relay_exchange,
                              relay_routing_key,
                              last_step))
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
        src_exchange = ""
        src_routing_key = ""
        last_step = "start"

        try:

            last_step = "finding source exchange"
            src_exchange = get_exchange_from_msg(message)

            last_step = "finding source routing key"
            src_routing_key = get_routing_key_from_msg(message)

            if self.verbose:
                log.info(("default handle_message - "
                          "processing - msg={} "
                          "from_ex={} from_rk={}")
                         .format(body,
                                 src_exchange,
                                 src_routing_key))
            else:
                if "msg_id" in body:
                    log.info(("hd msg={} "
                              "from_ex={} from_rk={}")
                             .format(body["msg_id"],
                                     src_exchange,
                                     src_routing_key))
                else:
                    log.info(("hd msg={} "
                              "from_ex={} from_rk={}")
                             .format(str(body)[0:30],
                                     src_exchange,
                                     src_routing_key))
            # end of logging for verbose

            handler_success = True
            should_ack = True

            if self.use_relay_handler:

                last_step = "relay start"

                if self.relay_exchange or self.relay_routing_key:
                    last_step = ("use_relay_handler={} is invalid") \
                                 .format(self.use_relay_handler)
                    log.debug(("relay use_relay_handler={}")
                              .format(self.use_relay_handler.__name__))

                    last_step = "relay check - handler start"
                    relay_success = self.use_relay_handler(
                                        body=body,
                                        message=message,
                                        relay_exchange=self.relay_exchange,
                                        relay_routing_key=self.relay_routing_key,
                                        serializer=self.relay_serializer)
                    last_step = "relay check - handler done"
                    relay_ran = True
                else:
                    relay_success = True
                # end of trying to relay

                last_step = "relay done"

            else:
                relay_success = True
            # end of relay handling

        except Exception as e:
            handler_success = False
            log.error(("Failed RelayWorker.handle_message "
                       "last_step={} with ex={} body={}")
                      .format(last_step,
                              e,
                              body))
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
