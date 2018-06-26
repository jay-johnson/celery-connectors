import os
import datetime
import uuid
import random
from spylunking.log.setup_logging import test_logger
from celery_connectors.utils import get_percent_done
from celery_connectors.utils import ev
from tests.base_test import BaseTestCase
import ecomm_app.ecommerce.tasks


log = test_logger(
    name='load-test-rabbit-worker')


class LoadTestWorkerRabbitMQConsuming(BaseTestCase):

    def build_user_conversion_event_msg(self,
                                        test_values,
                                        now=datetime.datetime.now().isoformat()):
        body = {"account_id": 777,
                "subscription_id": 888,
                "stripe_id": 999,
                "product_id": "XYZ",
                "simulate_processing_lag": random.uniform(1.0, 5.0),
                "msg_id": str(uuid.uuid4()),
                "created": now}

        return body
    # end of build_user_conversion_event_msg

    def test_rabbitmq_consuming(self):

        # Integration Test the Consuming Worker with 50,0000 messages
        # This test just uses send_task for publishing
        num_to_consume = 50000
        num_sent = 0
        num_to_send = num_to_consume
        msgs_to_send = []

        msgs_by_id = {}

        not_done_publishing = True

        test_values = {"test_name": "large messages"}

        if len(msgs_to_send) == 0:
            while len(msgs_to_send) != num_to_send:
                test_msg = self.build_user_conversion_event_msg(test_values)
                msgs_to_send.append(test_msg)
                msgs_by_id[test_msg["msg_id"]] = False
        # end of building messages before slower publishing calls

        pub_auth_url = ev("RELAY_WORKER_BROKER_URL",
                          "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
        path_to_config_module = "ecomm_app.ecommerce.celeryconfig_pub_sub"

        app = ecomm_app.ecommerce.tasks.get_celery_app(
                name="demo",
                auth_url=pub_auth_url,
                path_to_config_module=path_to_config_module)

        task_name = "ecomm_app.ecommerce.tasks.handle_user_conversion_events"

        source_id = {"msg_proc": ev("TEST_RELAY_NAME",
                                    "test_ecomm_relay")}
        result = None

        log.info(("Sending broker={}")
                 .format(app.conf.broker_url))

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

            result = app.send_task(task_name, (msg_body, source_id))

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
                          "{}/{} messages result={}")
                         .format(get_percent_done(num_sent,
                                                  len(msgs_to_send)),
                                 num_sent,
                                 num_to_send,
                                 result))

                not_done_publishing = False
            # if should stop

        # end of not_done_publishing

        assert(num_sent == num_to_consume)

        log.info("")
        os.system("list-queues.sh")
        log.info("")

    # end of test_rabbitmq_consuming

# end of LoadTestWorkerRabbitMQConsuming
