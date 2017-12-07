# -*- coding: utf-8 -*-
import logging
import unittest
import time
from celery_connectors.utils import get_percent_done
from tests.base_test import BaseTestCase

log = logging.getLogger(__file__)


class TestConsumeLargeNumberOfMessages(BaseTestCase):

    def test_consuming_large_number_of_messages(self):

        # Test the Publisher and Subscriber with 50,0000 messages
        # and verify each unique message id was consumed
        # default is using the rabbitmq broker
        num_to_consume = 50000
        num_sent = 0
        num_to_send = num_to_consume
        num_consumed = 0
        msgs_to_send = []
        msgs_received = []

        msgs_by_id = {}

        self.exchange_name = "test_large_num_1"
        self.routing_key = "test_large_num_1.orders"
        self.queue_name = "test_large_num_1.orders"

        class TestMessageProcessor:

            def __init__(self,
                         should_consume=1,
                         test_id=None,
                         stop_after_num=-1,
                         validate_for_test=False):

                self.num_consumed = 0
                self.should_consume = should_consume
                self.stop_after_num = stop_after_num
                self.expected_test_id = test_id

                self.recv_msgs = []
                self.validate_for_test = validate_for_test

            # end of __init__

            def process_message(self, body, message):
                self.num_consumed += 1

                test_id = "unknown"
                if "test_id" in body:
                    test_id = body["test_id"]

                # validate we're not crossing test streams
                if self.validate_for_test and test_id != self.expected_test_id:
                    log.error(("Test={} consumed a message "
                               "from another test={} - please "
                               "restart rabbitmq or clean up "
                               " the queue and try again")
                              .format(self.expected_test_id,
                                      test_id))

                    assert(test_id == self.expected_test_id)
                # end of validating the test_id matches the msg's test_id

                log.debug(("test={} Consumed message "
                           "{}/{} acking")
                          .format(test_id,
                                  self.num_consumed,
                                  self.should_consume))

                msgs_received.append(body)

                message.ack()
            # end of process_message

            def get_received_messages(self):
                return self.recv_msgs
            # end of get_received_messages

        # end of TestMessageProcessor

        log.info(("Publishing {}/{} "
                  "broker={}")
                 .format(num_sent,
                         num_to_send,
                         self.pub_auth_url))

        pub_retry = True
        not_done_publishing = True
        not_done_subscribing = True

        test_values = {"test_name": "large messages"}

        if len(msgs_to_send) == 0:
            while len(msgs_to_send) != num_to_send:
                test_msg = self.build_msg(test_values)
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
                         retry=True)

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

        log.info(("Creating Consumer "
                  "{}/{} messages")
                 .format(num_consumed,
                         num_to_consume))

        test_consumer = TestMessageProcessor(should_consume=num_to_consume,
                                             test_id=self.test_id,
                                             stop_after_num=-1)

        log.info(("Starting Consume "
                  "{}/{} messages")
                 .format(num_consumed,
                         num_to_consume))

        last_num_done = 0

        while not_done_subscribing:

            if (num_consumed % 1000 == 0) and num_consumed > 0:
                log.info(("Consumed {} for "
                          "{}/{} messages")
                         .format(get_percent_done(num_consumed,
                                                  num_to_consume),
                                 num_consumed,
                                 num_to_consume))
            # end of if print for tracing

            self.consume(callback=test_consumer.process_message,
                         queue=self.queue_name,
                         exchange=None,
                         routing_key=None,
                         serializer=self.sub_serializer,
                         heartbeat=60,
                         time_to_wait=2.0)

            num_consumed = len(msgs_received)

            if num_consumed >= num_to_consume and last_num_done == num_consumed:
                log.info(("Consumed {} ALL "
                          "{}/{} messages")
                         .format(get_percent_done(num_consumed,
                                                  num_to_consume),
                                 num_consumed,
                                 num_to_consume))

                not_done_subscribing = False
            else:

                # was there something in the queue already?
                if last_num_done == num_consumed:
                    # if not sleep it out
                    log.info(("Consumed {} "
                              "{}/{} messages")
                             .format(get_percent_done(num_consumed,
                                                      num_to_consume),
                                     num_consumed,
                                     num_to_consume))
                # end of checking if something was found or not

            # if should stop

            last_num_done = num_consumed

        # end of not_done_subscribing

        log.info(("test={} consumed={} "
                  "out of queue={}")
                 .format(self.test_id,
                         len(msgs_received),
                         self.queue_name))

        # find test messages that were sent and validate the msg id was from
        # this test
        for consumed_msg in msgs_received:
            consumed_msg_id = consumed_msg["msg_id"]
            if consumed_msg_id in msgs_by_id:
                msgs_by_id[consumed_msg_id] = True
        # end of for all consumed messages

        num_valid_messages = 0

        for msg_id in msgs_by_id:
            if not msg_id:
                log.error(("FAILED to find "
                           "test_id={} msg_id={}")
                          .format(self.test_id,
                                  msg_id))
                assert(msg_id)
            else:
                num_valid_messages += 1
        # end of for validating all the messages were found in the queue

        assert(num_valid_messages == num_to_consume)

    # end of test_consuming_large_number_of_messages

# end of TestConsumeLargeNumberOfMessages
