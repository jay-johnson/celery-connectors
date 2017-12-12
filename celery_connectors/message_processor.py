import datetime
import logging
from celery_connectors.utils import ev
from celery_connectors.kombu_subscriber import KombuSubscriber
from celery_connectors.publisher import Publisher

log = logging.getLogger("message-processor")


class MessageProcessor:

    def __init__(self,
                 name="message-processor",
                 sub_auth_url=ev("SUB_BROKER_URL", "redis://localhost:6379/0"),
                 sub_ssl_options={},
                 sub_serializer="application/json",
                 sub_silent=False,
                 pub_auth_url=ev("PUB_BROKER_URL", "redis://localhost:6379/0"),
                 pub_ssl_options={},
                 pub_serializer="json",
                 pub_silent=False):

        self.name = name
        self.recv_msgs = []
        self.sub_auth_url = sub_auth_url
        self.pub_auth_url = pub_auth_url
        self.sub_ssl_options = sub_ssl_options
        self.pub_ssl_options = pub_ssl_options
        self.sub_serializer = sub_serializer
        self.pub_serializer = pub_serializer
        self.pub_queue_name = None

        self.sub = None
        self.pub = None

        self.exchange = None
        self.exchange_name = ""
        self.queue = None
        self.queue_name = ""
        self.routing_key = None
        self.pub_routing_key = None
        self.pub_hook_version = 1

        self.sub_verbose = not sub_silent
        self.pub_verbose = not pub_silent

    # end of __init__

    def build_publish_node(self, body, data):
        publish_hook_body = {
            "org_msg": body,
            "data": data,
            "hook_created": datetime.datetime.now().isoformat(),
            "source": self.name,
            "version": self.pub_hook_version
        }
        return publish_hook_body
    # end of build_publish_node

    def process_message(self, body, message):
        log.info(("{} proc start - msg body={}")
                 .format(self.name, body))

        self.recv_msgs.append(body)

        if self.exchange_name:

            processing_data = {}

            if self.pub_verbose:
                log.info(("{} pub-hook - build - "
                          "hook msg body")
                         .format(self.name))

            publish_hook_body = self.build_publish_node(body,
                                                        data=processing_data)

            if self.pub_verbose:
                log.info(("{} pub-hook - send - "
                          "exchange={} rk={} sz={}")
                         .format(self.name,
                                 self.exchange_name,
                                 self.routing_key,
                                 self.pub_serializer))

            try:
                publish_hook_result = self.get_pub().publish(body=publish_hook_body,
                                                             exchange=self.exchange_name,
                                                             routing_key=self.routing_key,
                                                             queue=self.routing_key,
                                                             serializer=self.pub_serializer,
                                                             retry=True)
                if self.pub_verbose:
                    log.info(("{} pub-hook - send - done "
                              "exchange={} rk={} res={}")
                             .format(self.name,
                                     self.exchange_name,
                                     self.routing_key,
                                     publish_hook_result))

            except Exception as hookfailed:
                log.info(("{} Non-fatal - publish hook failed " +
                          "body={} exchange={} rk={} sz={} ex={}")
                         .format(self.name,
                                 body,
                                 self.exchange_name,
                                 self.routing_key,
                                 self.pub_serializer,
                                 hookfailed))
        else:
            log.info(("No auto-caching or pub-hook "
                      "set exchange={}")
                     .format(self.exchange))
        # end of send to publisher

        message.ack()

        log.info(("{} proc done - msg")
                 .format(self.name))
    # end of process_message

    def get_pub(self):
        if not self.pub:
            self.pub = Publisher("msg-pub",
                                 self.pub_auth_url,
                                 self.pub_ssl_options)
        return self.pub
    # end of get_pub

    def get_sub(self):
        if not self.sub:
            self.sub = KombuSubscriber("msg-sub",
                                       self.sub_auth_url,
                                       self.sub_ssl_options)
        return self.sub
    # end of get_sub

    def consume_queue(self,
                      queue,
                      exchange,
                      routing_key=None,
                      heartbeat=60,
                      expiration=None,
                      pub_serializer="application/json",
                      sub_serializer="application/json",
                      pub_queue_name=None,
                      seconds_to_consume=1.0,
                      forever=True,
                      silent=False,
                      callback=None):

        self.queue_name = queue
        self.exchange_name = exchange
        self.routing_key = routing_key
        self.pub_queue_name = pub_queue_name
        self.pub_serializer = pub_serializer
        self.sub_serializer = sub_serializer
        sub_silent = silent

        use_callback = self.process_message
        if callback:
            use_callback = callback

        log.info(("{} START - consume_queue={} "
                  "rk={} callback={}")
                 .format(self.name,
                         self.queue_name,
                         self.routing_key,
                         use_callback.__name__))

        not_done = True
        while not_done:

            self.get_sub().consume(callback=use_callback,
                                   queue=self.queue_name,
                                   exchange=None,
                                   routing_key=None,
                                   serializer=self.sub_serializer,
                                   heartbeat=heartbeat,
                                   forever=forever,
                                   time_to_wait=seconds_to_consume,
                                   silent=sub_silent)

            if not forever:
                not_done = False
            # if not forever

        # end of while loop

        log.info(("{} DONE - consume_queue={} rk={}")
                 .format(self.name,
                         self.queue_name,
                         self.routing_key))

    # end of consume_queue

# end of MessageProcessor
