# -*- coding: utf-8 -*-
import logging
from celery import Celery
from celery import bootsteps
from kombu import Queue, Exchange, Consumer
from celery_connectors.utils import ev
from celery_connectors.logging.setup_logging import setup_logging

setup_logging()


class Subscriber:

    def __init__(self,
                 name=ev("SUBSCRIBER_NAME", "celery-subscriber"),
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

        # allow passing in an initalized Celery application
        if app:
            self.subscriber_app = app
        else:
            self.subscriber_app = Celery()

        self.subscriber_app.conf.broker_url = self.auth_url

        self.exchange = None
        self.consume_from_queues = []

    # end of __init__

    def setup_routing(self, ex_name, consume_queue_names, routing_key=None):

        self.exchange = None
        if routing_key:
            self.log.debug("creating Exchange={} topic for rk={}".format(ex_name, routing_key))
            self.exchange = Exchange(ex_name, type="topic")
        else:
            self.log.debug("creating Exchange={} direct".format(ex_name, routing_key))
            self.exchange = Exchange(ex_name, type="direct")
        # end of if/else

        self.consume_from_queues = []
        for queue_name in consume_queue_names:

            new_queue = None
            if routing_key:
                self.log.debug(("creating Queue={} topic rk={} from Exchange={}")
                               .format(queue_name,
                                       routing_key,
                                       ex_name))
                new_queue = Queue(queue_name, exchange=self.exchange, routing_key=routing_key)
            else:
                self.log.debug(("creating Queue={} direct from Exchange={}")
                               .format(queue_name,
                                       ex_name))
                new_queue = Queue(queue_name, exchange=self.exchange)
            # end of handling queues with direct/topic routing

            self.consume_from_queues.append(new_queue)
        # end of building new consume queues

        self.subscriber_app.conf.tasks_queues = self.consume_from_queues

        self.state = "ready"
    # end of setup_routing

    def consume(self,
                callback,
                queue,
                exchange=None,
                routing_key=None):

        """
        Redis does not have an Exchange or Routing Keys, but RabbitMQ does.

        Redis producers uses only the queue name to both publish and consume messages:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#configuration
        """

        if self.state != "ready":
            if exchange and routing_key:
                self.setup_routing(exchange, [queue], routing_key)
            else:
                self.setup_routing(queue, [queue])
        # end of initializing for the first time

        self.log.info(("{} - Subscribed to Exchange={} with routes to queues={} with callback={}")
                      .format(self.state.upper(),
                              self.exchange.name,
                              len(self.consume_from_queues),
                              callback))

        consume_from_queues = self.consume_from_queues

        class ConnectorConsumer(bootsteps.ConsumerStep):

            def get_consumers(self, channel):
                return [Consumer(channel,
                                 queues=consume_from_queues,
                                 callbacks=[callback],
                                 accept=["json"])]
            # end of get_consumer

        # end of ConnectorConsumer

        self.subscriber_app.steps["consumer"].add(ConnectorConsumer)

    # end of consume

# end of Subscriber
