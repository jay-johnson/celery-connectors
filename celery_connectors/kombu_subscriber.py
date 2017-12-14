import socket
import logging
import time
from kombu import Connection, Consumer, Queue, Exchange
from celery_connectors.utils import ev
from celery_connectors.utils import calc_backoff_timer

log = logging.getLogger("kombu-subscriber")


class KombuSubscriber:

    def __init__(self,
                 name=ev("SUBSCRIBER_NAME", "kombu-subscriber"),
                 auth_url=ev("BROKER_URL", "redis://localhost:6379/0"),
                 ssl_options={},
                 max_general_failures=-1):  # infinite retries

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

        self.conn = None
        self.new_conn = None
        self.channel = None
        self.consumer = None
        self.process_message_callback = None
        self.drain_time = 1.0
        self.num_setup_failures = 0
        self.num_consume_failures = 0
        self.max_general_failures = max_general_failures

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
                      serializer="application/json",
                      transport_options={}):

        self.state = "not_ready"
        self.exchange = None
        self.exchange_name = exchange
        self.routing_key = routing_key
        self.serializer = serializer
        self.queue = None

        if self.routing_key:
            log.debug(("creating Exchange={} topic for rk={}")
                      .format(self.exchange_name, self.routing_key))
            self.exchange = Exchange(self.exchange_name, type="topic")
        else:
            log.debug(("creating Exchange={} direct")
                      .format(self.exchange_name, self.routing_key))
            self.exchange = Exchange(self.exchange_name, type="direct")
        # end of if/else

        self.consume_from_queues = []
        for queue_name in consume_queue_names:

            new_queue = None
            if self.routing_key:
                log.debug(("creating Queue={} topic rk={} from Exchange={}")
                          .format(queue_name,
                                  self.routing_key,
                                  self.exchange_name))
                new_queue = Queue(queue_name, exchange=self.exchange, routing_key=self.routing_key)
            else:
                log.debug(("creating Queue={} direct from Exchange={}")
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
        self.conn = Connection(self.auth_url,
                               heartbeat=heartbeat,
                               transport_options=transport_options)

        self.channel = self.conn.channel()

        self.process_message_callback = process_message_callback

        log.debug(("creating kombu.Consumer "
                   "broker={} ssl={} ex={} rk={} "
                   "queue={} serializer={}")
                  .format(self.auth_url,
                          self.ssl_options,
                          self.exchange_name,
                          self.routing_key,
                          self.queue_name,
                          self.serializer))

        self.consumer = Consumer(self.conn,
                                 queues=self.consume_from_queues,
                                 auto_declare=True,
                                 callbacks=[self.process_message_callback],
                                 accept=["{}".format(self.serializer)])

        log.debug(("creating kombu.Exchange={}")
                  .format(self.exchange))

        self.consumer.declare()

        log.debug(("creating kombu.Queue={}")
                  .format(self.queue_name))

        self.queue.maybe_bind(self.conn)
        self.queue.declare()

        self.consumer.consume()

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

    def try_consume_from_queue(self,
                               time_to_wait=5.0):

        success = False
        try:
            self.consumer.consume()
            log.debug(("draining events time_to_wait={}")
                      .format(time_to_wait))
            self.conn.drain_events(timeout=time_to_wait)
            self.num_consume_failures = 0
            success = True
        except socket.timeout as t:
            log.debug(("detected socket.timeout - "
                       "running heartbeat check={}")
                      .format(t))
            self.conn.heartbeat_check()
        except ConnectionRefusedError:  # noqa
            sleep_duration = calc_backoff_timer(num=self.num_consume_failures)
            log.debug(("{} - kombu.subscriber - consume - hit "
                       "connection refused sleep seconds={}")
                      .format(self.name,
                              sleep_duration))
            self.state = "connection refused"
            self.num_consume_failures += 1
            time.sleep(sleep_duration)
        except ConnectionResetError:  # noqa
            sleep_duration = calc_backoff_timer(num=self.num_consume_failures)
            log.info(("{} - kombu.subscriber - consume - hit "
                      "connection reset sleep seconds={}")
                     .format(self.name,
                             sleep_duration))
            self.state = "connection reset"
            self.num_consume_failures += 1
            time.sleep(sleep_duration)
        except Exception as e:
            sleep_duration = calc_backoff_timer(num=self.num_consume_failures)
            log.info(("{} - kombu.subscriber - consume - hit "
                      "general exception={} queue={} sleep seconds={}")
                     .format(self.name,
                             e,
                             self.queue_name,
                             sleep_duration))
            self.state = "general error - consume"
            self.num_consume_failures += 1
            time.sleep(sleep_duration)
        # end of supported errors
        # end of try/ex

        return success
    # end of try_consume_from_queue

    def restore_connection(self,
                           callback,
                           queue,
                           exchange=None,
                           routing_key=None,
                           heartbeat=60,
                           serializer="application/json",
                           silent=False,
                           transport_options={},
                           *args,
                           **kwargs):

        ready_for_consume = False

        if self.state != "ready" or queue != self.queue_name:
            if not silent:
                log.info("setup routing")

            try:
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

                ready_for_consume = True
                self.num_setup_failures = 0
                self.num_consume_failures = 0
            except ConnectionRefusedError:  # noqa
                sleep_duration = calc_backoff_timer(num=self.num_setup_failures)
                log.info(("{} - kombu.subscriber - setup - hit "
                          "connection refused sleep seconds={}")
                         .format(self.name,
                                 sleep_duration))

                self.state = "connection refused"
                self.num_setup_failures += 1
                time.sleep(sleep_duration)
                ready_for_consume = False
            except Exception as e:
                sleep_duration = calc_backoff_timer(num=self.num_setup_failures)
                log.info(("{} - kombu.subscriber - setup - hit "
                          "exception={} queue={} sleep seconds={}")
                         .format(self.name,
                                 e,
                                 self.queue_name,
                                 sleep_duration))
                self.state = "general error - setup"
                self.num_setup_failures += 1
                ready_for_consume = False
                time.sleep(sleep_duration)
            # end of initializing connection
        # end of if need to restore connection for a
        # broker restart or queues are deleted/need to be created
        else:
            ready_for_consume = True
        # esle we're already to go

        return ready_for_consume
    # end of restore_connection

    def consume(self,
                callback,
                queue,
                exchange=None,
                routing_key=None,
                heartbeat=60,
                serializer="application/json",
                time_to_wait=5.0,
                forever=False,
                silent=False,
                transport_options={},
                *args,
                **kwargs):

        """
        Redis does not have an Exchange or Routing Keys, but RabbitMQ does.

        Redis producers uses only the queue name to both publish and consume messages:
        http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#configuration
        """

        if not callback:
            log.info(("Please pass in a valid callback "
                      "function or class method"))
            return

        not_done = True
        self.num_setup_failures = 0
        self.num_consume_failures = 0

        while not_done:

            # each loop start as the incoming forever arg
            not_done = forever

            ready_for_consume = self.restore_connection(
                                        callback=callback,
                                        queue=queue,
                                        exchange=exchange,
                                        routing_key=routing_key,
                                        heartbeat=heartbeat,
                                        serializer=serializer,
                                        silent=silent,
                                        transport_options=transport_options)

            if ready_for_consume:

                if not forever and not silent:
                    log.info(("{} - kombu.subscriber queues={} "
                              "consuming with callback={}")
                             .format(self.name,
                                     self.queue_name,
                                     callback.__name__))

                self.try_consume_from_queue(time_to_wait=time_to_wait)
            # end of trying to consume

            # only allow error-retry-stop if not going forever
            if not forever and self.max_general_failures > 0:

                if self.num_setup_failures > self.max_general_failures \
                   or self.num_consume_failures > self.max_general_failures:

                    log.error(("Stopping consume for max={} "
                               "setup_failures={} consume_failures={} queue={}")
                              .format(self.max_general_failures,
                                      self.num_setup_failures,
                                      self.num_consume_failures,
                                      self.queue_name))

                    not_done = False
                # if we're over the retry limits

            else:
                if ev("TEST_STOP_DONE", "0") == "1":
                    not_done = False
                else:
                    not_done = True
            # if not forever

        # end of hearbeat and event checking

    # end of consume

# end of KombuSubscriber
