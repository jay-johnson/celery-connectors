# -*- coding: utf-8 -*-
import logging
from kombu import Queue, Exchange, Producer, Connection
from celery_connectors.utils import ev
from celery_connectors.logging.setup_logging import setup_logging

setup_logging()


class Publisher:

    def __init__(self,
                 name=ev("PUBLISHER_NAME", "kombu-publisher"),
                 auth_url=ev("BROKER_URL", "redis://localhost:6379/0"),
                 ssl_options={}):

        """
        Available Transports:
        https://github.com/celery/kombu#transport-comparison
        """

        self.state = "not_ready"
        self.name = name
        self.log = logging.getLogger(self.name)
        self.auth_url = auth_url
        self.ssl_options = ssl_options

        self.exchange = None
        self.queue = None
        self.declare_entities = []
        self.conn = None
        self.channel = None
        self.producer = None

        self.exchange_name = ""
        self.exchange_type = "direct"
        self.queue_name = ""
        self.routing_key = ""
        self.serializer = "json"

    # end of __init__

    def setup_routing(self, exchange_name, queue_name, routing_key, serializer="json", on_return=None):

        self.exchange_name = exchange_name
        self.exchange = None
        self.routing_key = routing_key
        self.queue_name = queue_name
        self.serializer = serializer

        if self.routing_key:
            self.log.debug("creating Exchange={} topic rk={}".format(self.exchange_name, self.routing_key))
            self.exchange_type = "topic"
        else:
            self.log.debug("creating Exchange={} direct".format(self.exchange_name, self.routing_key))
            self.exchange_type = "direct"
        # end of if/else

        self.exchange = Exchange(self.exchange_name, type=self.exchange_type)

        self.queue = Queue(self.queue_name, exchange=self.exchange, routing_key=self.routing_key)

        self.declare_entities = [
            self.exchange,
            self.queue
        ]

        # https://redis.io/topics/security
        #
        # Redis does not support encryption, but I would like to try out ssl-termination
        # using an haproxy/nginx container running as an ssl-proxy to see if this works.

        # import ssl
        # Connection("amqp://", login_method='EXTERNAL', ssl={
        #               "ca_certs": '/etc/pki/tls/certs/something.crt',
        #               "keyfile": '/etc/something/system.key',
        #               "certfile": '/etc/something/system.cert',
        #               "cert_reqs": ssl.CERT_REQUIRED,
        #          })
        #
        self.conn = Connection(self.auth_url)
        self.channel = self.conn.channel()
        self.log.debug(("creating kombu.Producer broker={} ssl={} ex={} rk={} serializer={}")
                       .format(self.auth_url,
                               self.ssl_options,
                               self.exchange_name,
                               self.routing_key,
                               self.serializer))

        self.producer = Producer(channel=self.channel,
                                 exchange=self.exchange,
                                 routing_key=self.routing_key,
                                 serializer=self.serializer,
                                 on_return=None)

        self.log.debug("creating kombu.Exchange={}".format(self.exchange))
        self.producer.declare()

        self.log.debug("creating kombu.Queue={}".format(self.queue_name))
        self.queue.maybe_bind(self.conn)
        self.queue.declare()

        self.state = "ready"
    # end of setup_routing

    def publish(self,
                body,
                exchange,
                routing_key,
                queue,
                priority=0,
                ttl=None,
                serializer="json",
                retry=True):

        """
        Redis does not have an Exchange or Routing Keys, but RabbitMQ does.

        Redis producers uses only the queue name to both publish and consume messages:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#configuration
        """

        if self.state != "ready":
            self.setup_routing(exchange,
                               queue,
                               routing_key,
                               serializer)
        # end of initializing for the first time

        self.log.info(("{} - PUB - exch={} queue={} body={}")
                      .format(self.state.upper(),
                              self.exchange.name,
                              self.queue,
                              body))

        # http://docs.celeryproject.org/projects/kombu/en/latest/_modules/kombu/messaging.html#Producer.publish
        send_result = self.producer.publish(
            body=body,
            exchange=self.exchange.name,
            routing_key=self.routing_key,
            serializer=self.serializer,
            priority=priority,
            expiration=ttl,
            retry=True
        )

        self.log.debug(("{} - PUB DONE - exch={} queues={} body={}")
                       .format(self.state.upper(),
                               self.exchange.name,
                               self.queue,
                               body))

        return send_result
    # end of publish

# end of Publisher
