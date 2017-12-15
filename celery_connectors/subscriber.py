import logging
from celery import Celery
from celery import bootsteps
from kombu import Queue, Exchange, Consumer
from celery_connectors.utils import ev

log = logging.getLogger("celery-subscriber")


class Subscriber:

    def __init__(self,
                 name=ev("SUBSCRIBER_NAME", "celery-subscriber"),
                 auth_url=ev("BROKER_URL", "redis://localhost:6379/0"),
                 app=None,
                 ssl_options={},
                 transport_options={},
                 worker_log_format="%(asctime)s: %(levelname)s %(message)s",
                 **kwargs):

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
        self.auth_url = auth_url
        self.ssl_options = ssl_options
        self.transport_options = transport_options

        self.subscriber_app = None

        # allow passing in an initialized Celery application
        if app:
            self.subscriber_app = app
        else:
            self.subscriber_app = Celery()

        # update the celery configuration from the kwargs dictionary
        self.subscriber_app.conf.update(kwargs)

        # make sure to set the broker_url
        self.subscriber_app.conf.broker_url = self.auth_url
        self.subscriber_app.conf.worker_log_format = worker_log_format

        self.exchange = None
        self.consume_from_queues = []

    # end of __init__

    def setup_routing(self, ex_name, consume_queue_names, routing_key=None):

        self.exchange = None
        if routing_key:
            log.debug(("creating Exchange={} topic for rk={}")
                      .format(ex_name,
                              routing_key))
            self.exchange = Exchange(ex_name, type="topic")
        else:
            log.debug(("creating Exchange={} direct")
                      .format(ex_name,
                              routing_key))
            self.exchange = Exchange(ex_name,
                                     type="direct")
        # end of if/else

        self.consume_from_queues = []
        for queue_name in consume_queue_names:

            new_queue = None
            if routing_key:
                log.debug(("creating Queue={} topic rk={} from Exchange={}")
                          .format(queue_name,
                                  routing_key,
                                  ex_name))
                new_queue = Queue(queue_name,
                                  exchange=self.exchange,
                                  routing_key=routing_key)
            else:
                log.debug(("creating Queue={} direct from Exchange={}")
                          .format(queue_name,
                                  ex_name))
                new_queue = Queue(queue_name, exchange=self.exchange)
            # end of handling queues with direct/topic routing

            self.consume_from_queues.append(new_queue)
        # end of building new consume queues

        self.subscriber_app.conf.tasks_queues = self.consume_from_queues
        self.subscriber_app.conf.broker_transport_options = self.transport_options

        self.state = "ready"
    # end of setup_routing

    def consume(self,
                callback,
                queue=None,
                queues=[],
                exchange=None,
                routing_key=None,
                silent=False,
                prefetch_count=1,  # only fetch one message off the queue
                auto_declare=True):

        """
        Redis does not have an Exchange or Routing Keys, but RabbitMQ does.

        Redis producers uses only the queue name to both publish and consume messages:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#configuration
        """

        if not callback:
            log.info(("Please pass in a valid callback "
                      "function or class method"))
            return

        if not queue and len(queues) == 0:
            log.info(("Please pass in a valid queue name"
                      "or list of queue names"))
            return

        if self.state != "ready":
            use_queues = [queue]
            if len(queues) > 0:
                use_queues = queues

            if exchange and routing_key:
                self.setup_routing(exchange, use_queues, routing_key)
            else:
                self.setup_routing(queue, use_queues)
        # end of initializing for the first time

        if not silent:
            log.info(("Subscribed to Exchange={} with "
                      "routes to queues={} with callback={} "
                      "prefetch_count={}")
                     .format(self.exchange.name,
                             len(self.consume_from_queues),
                             callback.__name__,
                             prefetch_count))

        consume_from_queues = self.consume_from_queues

        # http://docs.celeryproject.org/en/latest/userguide/extending.html
        class ConnectorConsumer(bootsteps.ConsumerStep):

            def get_consumers(self, channel):

                # http://docs.celeryproject.org/projects/kombu/en/latest/userguide/consumers.html
                return [Consumer(channel,
                                 queues=consume_from_queues,
                                 auto_declare=auto_declare,
                                 prefetch_count=prefetch_count,
                                 callbacks=[callback],
                                 accept=["json"])]
            # end of get_consumer

        # end of ConnectorConsumer

        self.subscriber_app.steps["consumer"].add(ConnectorConsumer)

    # end of consume

# end of Subscriber
