import os
import logging
import datetime
import uuid
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.utils import get_percent_done
from celery_connectors.utils import ev
from tests.base_test import BaseTestCase

setup_logging()

log = logging.getLogger("load-test-rabbit-relay")


class LoadTestRelayRabbitMQConsuming(BaseTestCase):

    def build_user_conversion_event_msg(self,
                                        test_values,
                                        now=datetime.datetime.now().isoformat()):
        body = {"account_id": 777,
                "subscription_id": 888,
                "stripe_id": 999,
                "product_id": "XYZ",
                "msg_id": str(uuid.uuid4()),
                "created": now}

        return body
    # end of build_user_conversion_event_msg

    def test_rabbitmq_consuming(self):

        # Integration Test the Relay Processor
        # This test just fills the queue for processing
        num_to_consume = 50000
        num_sent = 0
        num_to_send = num_to_consume
        msgs_to_send = []

        msgs_by_id = {}

        self.exchange_name = ev("LOAD_TEST_EXCHANGE",
                                "user.events")
        self.routing_key = ev("LOAD_TEST_ROUTING_KEY",
                              "user.events.conversions")
        self.queue_name = ev("LOAD_TEST_QUEUE",
                             "user.events.conversions")

        log.info(("Publishing {}/{} "
                  "ex={} rk={} broker={}")
                 .format(num_sent,
                         num_to_send,
                         self.exchange_name,
                         self.routing_key,
                         self.pub_auth_url))

        pub_retry = True
        not_done_publishing = True

        test_values = {"test_name": "large messages"}

        if len(msgs_to_send) == 0:
            while len(msgs_to_send) != num_to_send:

                test_msg = self.build_user_conversion_event_msg(test_values)
                msgs_to_send.append(test_msg)
                msgs_by_id[test_msg["msg_id"]] = False
        # end of building messages before slower publishing calls

        while not_done_publishing:

            if (num_sent % 1000 == 0) and num_sent > 0:
                log.info(("Published {} for "
                          "{}/{} messages")
                         .format(get_percent_done(num_sent,
                                                  num_to_send),
                                 num_sent,
                                 num_to_send))
            # end of if print for tracing

            msg_body = None
            if num_sent < len(msgs_to_send):
                msg_body = msgs_to_send[num_sent]

            self.publish(body=msg_body,
                         exchange=self.exchange_name,
                         routing_key=self.routing_key,
                         queue=self.queue_name,
                         priority=0,
                         ttl=None,
                         serializer=self.pub_serializer,
                         retry=pub_retry)

            num_sent += 1

            if num_sent >= num_to_send:
                log.info(("Published {} ALL "
                          "{}/{} messages")
                         .format(get_percent_done(num_sent,
                                                  num_to_send),
                                 num_sent,
                                 num_to_send))

                not_done_publishing = False
            elif num_sent >= len(msgs_to_send):
                log.info(("Published {} all "
                          "{}/{} messages")
                         .format(get_percent_done(num_sent,
                                                  len(msgs_to_send)),
                                 num_sent,
                                 num_to_send))

                not_done_publishing = False
            # if should stop

        # end of not_done_publishing

        assert(num_sent == num_to_consume)

        os.system("list-queues.sh")

        log.info("")
        log.info(("display messages in the queues "
                  "with routing_key={} again with:")
                 .format(self.routing_key))
        log.info("list-queues.sh")
        log.info("")

    # end of test_rabbitmq_consuming

# end of LoadTestRelayRabbitMQConsuming
