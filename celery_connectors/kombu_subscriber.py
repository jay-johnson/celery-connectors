# -*- coding: utf-8 -*-
import socket
import logging
from kombu import Connection, Consumer, Queue, Exchange
from celery_connectors.utils import ev
from celery_connectors.logging.setup_logging import setup_logging

setup_logging()


class KombuSubscriber:

    def __init__(self,
                 name=ev("SUBSCRIBER_NAME", "kombu-subscriber"),
                 auth_url=ev("BROKER_URL", "redis://localhost:6379/0"),
                 app=None,
                 ssl_options={}):

        """
        Available Brokers:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html

        Redis:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html

        RabbitMQ:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html

        SQS:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/sqs.html
        """

        self.state = "not_ready"
        self.name = name
        self.log = logging.getLogger(self.name)
        self.auth_url = auth_url
        self.ssl_options = ssl_options

        self.subscriber_app = None

        self.exchange = None
        self.exchange_name = ""
        self.routing_key = ""
        self.serializer = "json"
        self.queue = None
        self.queue_name = ""
        self.consume_from_queues = []

    # end of __init__

    def setup_routing(self,
                      exchange,
                      consume_queue_names,
                      process_message_callback,
                      routing_key=None,
                      heartbeat=60,
                      serializer="application/json"):

        self.exchange = None
        self.exchange_name = exchange
        self.routing_key = routing_key
        self.serializer = serializer
        self.queue = None

        if self.routing_key:
            self.log.debug("creating Exchange={} topic for rk={}".format(self.exchange_name, self.routing_key))
            self.exchange = Exchange(self.exchange_name, type="topic")
        else:
            self.log.debug("creating Exchange={} direct".format(self.exchange_name, self.routing_key))
            self.exchange = Exchange(self.exchange_name, type="direct")
        # end of if/else

        self.consume_from_queues = []
        for queue_name in consume_queue_names:

            new_queue = None
            if self.routing_key:
                self.log.debug(("creating Queue={} topic rk={} from Exchange={}")
                               .format(queue_name,
                                       self.routing_key,
                                       self.exchange_name))
                new_queue = Queue(queue_name, exchange=self.exchange, routing_key=self.routing_key)
            else:
                self.log.debug(("creating Queue={} direct from Exchange={}")
                               .format(queue_name,
                                       self.exchange_name))
                new_queue = Queue(queue_name, exchange=self.exchange)
            # end of handling queues with direct/topic routing

            self.consume_from_queues.append(new_queue)

            if not self.queue:
                self.queue_name = queue_name
                self.queue = new_queue

        # end of building new consume queues

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
        self.conn = Connection(self.auth_url, heartbeat=heartbeat)
        self.channel = self.conn.channel()
        self.log.debug(("creating kombu.Consumer broker={} ssl={} ex={} rk={} queue={} serializer={}")
                       .format(self.auth_url,
                               self.ssl_options,
                               self.exchange_name,
                               self.routing_key,
                               self.queue_name,
                               self.serializer))

        self.consumer = Consumer(self.conn,
                                 queues=self.consume_from_queues,
                                 callbacks=[process_message_callback],
                                 accept=["{}".format(self.serializer)])

        self.log.debug("creating kombu.Exchange={}".format(self.exchange))
        self.consumer.declare()

        self.log.debug("creating kombu.Queue={}".format(self.queue_name))
        self.queue.maybe_bind(self.conn)
        self.queue.declare()

        self.state = "ready"
    # end of setup_routing

    def establish_connection(self):
        revived_connection = self.conn.clone()
        revived_connection.ensure_connection(max_retries=3)
        channel = revived_connection.channel()
        self.consumer.revive(channel)
        self.consumer.consume()
        return revived_connection
    # end of establish_connection

    def consume(self,
                callback,
                queue,
                exchange=None,
                routing_key=None,
                heartbeat=60,
                serializer="application/json",
                time_to_wait=1.0):

        """
        Redis does not have an Exchange or Routing Keys, but RabbitMQ does.

        Redis producers uses only the queue name to both publish and consume messages:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#configuration
        """

        if self.state != "ready":
            if exchange and routing_key:
                self.setup_routing(exchange,
                                   [queue],
                                   callback,
                                   routing_key,
                                   heartbeat=heartbeat,
                                   serializer=serializer)
            else:
                self.setup_routing(queue,
                                   [queue],
                                   callback,
                                   routing_key,
                                   heartbeat=heartbeat,
                                   serializer=serializer)
        # end of initializing for the first time

        not_done = True

        while not_done:
            self.log.info(("{} - kombu.subscriber queues={} wait={} callback={}")
                          .format(self.name,
                                  self.queue_name,
                                  time_to_wait,
                                  callback))

            self.new_conn = self.establish_connection()
            try:
                self.consumer.consume()

                self.log.debug("draining events time_to_wait={}".format(time_to_wait))
                self.new_conn.drain_events(timeout=time_to_wait)
            except socket.timeout:
                self.log.debug("heartbeat check")
                self.new_conn.heartbeat_check()
            except Exception as e:
                self.log.info(("{} - kombu.subscriber consume hit ex={} queue={}")
                              .format(self.name,
                                      e,
                                      queue_name))

            not_done = False
        # end of hearbeat and event checking

    # end of consume

# end of KombuSubscriber
