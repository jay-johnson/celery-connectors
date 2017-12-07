# -*- coding: utf-8 -*-
import logging
import unittest
import datetime
import uuid
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.utils import ev
from celery_connectors.publisher import Publisher
from celery_connectors.kombu_subscriber import KombuSubscriber

name = "base_test"

log = logging.getLogger(name)


class BaseTestCase(unittest.TestCase):

    debug = False

    exchange_name = ev("TEST_EXCHANGE", "test.events")
    queue_name = ev("TEST_QUEUE", "test.events.conversions")
    routing_key = ev("TEST_ROUTING_KEY", "test.events.conversions")

    exchange = None
    queue = None

    rabbitmq_auth_url = ev("TEST_RABBITMQ_BROKER_URL", "amqp://rabbitmq:rabbitmq@localhost:5672//")
    redis_auth_url = ev("TEST_REDIS_BROKER_URL", "redis://localhost:6379/0")

    pub_auth_url = rabbitmq_auth_url
    sub_auth_url = rabbitmq_auth_url

    pub_ssl_options = {}
    sub_ssl_options = {}

    pub_attrs = {}
    sub_attrs = {}

    pub_serializer = "json"
    sub_serializer = "application/json"

    test_body = {}
    test_id = str(uuid.uuid4()).replace("-", "")

    test_body = {"account_id": 123,
                 "subscription_id": 456,
                 "stripe_id": 789,
                 "product_id": "ABC"}

    pub_msgs = []
    sub_msgs = []

    last_pub_msg = None
    last_sub_msg = None
    last_sub_callback = None

    def setUp(self):
        if self.debug:
            print("setUp")

        self.last_pub_msg = None
        self.last_sub_msg = None
        self.pub = None
        self.sub = None
        self.pub_msgs = []
        self.sub_msgs = []

        self.exchange_name = ev("TEST_EXCHANGE", "test.events")
        self.routing_key = ev("TEST_ROUTING_KEY", "test.events.conversions")
        self.queue_name = ev("TEST_QUEUE", "test.events.conversions")

        self.exchange = None
        self.queue = None
        self.last_sub_callback = None

    # end of setUp

    def tearDown(self):
        if self.debug:
            print("tearDown")
        self.pub = None
        self.sub = None
        self.exchange = None
        self.queue = None
        self.last_sub_callback = None
    # end of tearDown

    def handle_message(self,
                       body,
                       msg):

        log.info(("test={} got "
                  "body={} msg={}")
                 .format(self,
                         test_id,
                         body,
                         msg))
    # end of handle_message

    def connect_pub(self,
                    auth_url=None,
                    ssl_options={},
                    attrs={}):

        use_auth_url = self.pub_auth_url
        use_ssl_options = self.pub_ssl_options
        use_pub_attrs = self.pub_attrs

        if auth_url:
            use_auth_url = auth_url
        if len(ssl_options) > 0:
            use_ssl_options = ssl_optios
        if len(ssl_options) > 0:
            use_pub_attrs = use_pub_attrs

        self.pub = Publisher("test-pub",
                             use_auth_url,
                             use_ssl_options)

    # end of connect_pub

    def connect_sub(self,
                    auth_url=None,
                    ssl_options={},
                    attrs={}):

        use_auth_url = self.sub_auth_url
        use_ssl_options = self.sub_ssl_options
        use_sub_attrs = self.sub_attrs

        if auth_url:
            use_auth_url = auth_url
        if len(ssl_options) > 0:
            use_ssl_options = ssl_optios
        if len(ssl_options) > 0:
            use_sub_attrs = use_sub_attrs

        self.sub = KombuSubscriber("test-sub",
                                   use_auth_url,
                                   use_ssl_options)
    # end of connect_sub

    def build_msg(self,
                  test_values={}):

        body = {"test_id": self.test_id,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                "msg_id": str(uuid.uuid4()).replace("-", ""),
                "test_values": test_values}

        return body
    # end of build_msg

    def consume(self,
                callback=None,
                queue=queue,
                exchange=exchange,
                routing_key=routing_key,
                serializer="application/json",
                heartbeat=60,
                time_to_wait=5.0,
                silent=True):

        if not callback:
            log.error(("Subscriber - Requires a callback handler for message"
                       "processing with signature definition: "
                       "def handle_message(self, body, message):")
                      .format(self.sub_auth_url,
                              self.sub_ssl_options))
            assert(callback)

        # if not connected, just connect with defaults
        if not self.sub:
            self.connect_sub()
            if not self.sub:
                log.error(("Subscriber - Failed to connect "
                           "to broker={} ssl={}")
                          .format(self.sub_auth_url,
                                  self.sub_ssl_options))
                assert(self.sub)

        if self.sub:

            self.sub.consume(callback=callback,
                             queue=queue,
                             exchange=exchange,
                             routing_key=routing_key,
                             serializer=serializer,
                             heartbeat=heartbeat,
                             time_to_wait=time_to_wait,
                             silent=silent)

        else:
            log.info("Sub is None already - client should not call consume")
    # end of consume

    def publish(self,
                body=None,
                exchange=exchange,
                routing_key=routing_key,
                queue=queue,
                priority=0,
                ttl=None,
                serializer="json",
                retry=True,
                silent=True):

        # if no body for the message
        if not body:
            log.error(("Publisher - requires argument: "
                       "body=some_dictionary to test"))
            assert(body)

        # if not connected, just connect with defaults
        if not self.pub:
            self.connect_pub()
            if not self.pub:
                log.error(("Publisher - Failed to connect "
                           "to broker={} ssl={}")
                          .format(self.pub_auth_url,
                                  self.pub_ssl_options))
                assert(self.pub)

        if self.pub:
            pub_result = self.pub.publish(body=body,
                                          exchange=exchange,
                                          routing_key=routing_key,
                                          queue=queue,
                                          serializer=serializer,
                                          priority=priority,
                                          ttl=ttl,
                                          retry=retry,
                                          silent=silent)
        else:
            log.info("Pub is None already - client should not call publish")
    # end of publish

# end of BaseTestCase
