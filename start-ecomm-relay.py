#!/usr/bin/env python

import uuid
import time
from datetime import datetime
from spylunking.log.setup_logging import build_colorized_logger
from celery_connectors.utils import ev
from celery_connectors.message_processor import MessageProcessor

# import the ecommerce tasks out of the demo dir
import ecomm_app.ecommerce.tasks


name = "ecomm-relay"
log = build_colorized_logger(
    name=name)

log.info("Start - {}".format(name))


def relay_callback(body, message):

    pub_auth_url = ev("RELAY_WORKER_BROKER_URL",
                      "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
    pub_backend_url = ev("RELAY_BACKEND_URL",
                         "redis://localhost:6379/12")
    path_to_config_module = ev("RELAY_CONFIG_MODULE",
                               "ecomm_app.ecommerce.celeryconfig_pub_sub")

    app = ecomm_app.ecommerce.tasks.get_celery_app(
            name=ev("RELAY_NAME", "ecomm-relay"),
            auth_url=pub_auth_url,
            backend_url=pub_backend_url,
            path_to_config_module=path_to_config_module)

    task_name = ev("RELAY_TASK_NAME",
                   "ecomm_app.ecommerce.tasks.handle_user_conversion_events")
    now = datetime.now().isoformat()
    body = {"account_id": 999,
            "subscription_id": 321,
            "stripe_id": 876,
            "created": now,
            "product_id": "JJJ",
            "version": 1,
            "org_msg": body,
            "msg_id": str(uuid.uuid4())}

    source_info = {"msg_proc": ev("RELAY_NAME",
                                  "ecomm_relay")}

    log.info(("Sending broker={} "
              "body={}")
             .format(app.conf.broker_url,
                     body))

    result = app.send_task(task_name, (body, source_info))

    if "simulate_processing_lag" in body:
        log.info(("task - {} - simulating processing"
                  "lag={} sleeping")
                 .format(task_name,
                         body["simulate_processing_lag"]))
        time.sleep(float(body["simulate_processing_lag"]))
    # end of handling adding artifical lag for testing Celery

    log.info(("Done with msg_id={} result={}")
             .format(body["msg_id"],
                     result.get()))

    # now that the message has been
    # sent to the celery ecomm worker
    # we can ack the message which
    # deletes it from the source queue
    # the message processor uses
    message.ack()

# end of relay_callback


# want to change where you're subscribing vs publishing?
sub_ssl_options = {}
sub_auth_url = ev("SUB_BROKER_URL",
                  "pyamqp://rabbitmq:rabbitmq@localhost:5672//")
pub_ssl_options = {}
pub_auth_url = ev("PUB_BROKER_URL",
                  "redis://localhost:6379/0")

# start the message processor
msg_proc = MessageProcessor(name=name,
                            sub_auth_url=sub_auth_url,
                            sub_ssl_options=sub_ssl_options,
                            pub_auth_url=pub_auth_url,
                            pub_ssl_options=pub_ssl_options)

# configure where this is consuming:
queue = ev("CONSUME_QUEUE", "user.events.conversions")

# Relay Publish Hook - sending to Redis
# where is it sending handled messages using a publish-hook or auto-caching:
exchange = ev("PUBLISH_EXCHANGE", "reporting.accounts")
routing_key = ev("PUBLISH_ROUTING_KEY", "reporting.accounts")

# set up the controls and long-term connection attributes
seconds_to_consume = 10.0
heartbeat = 60
serializer = "application/json"
pub_serializer = "json"
expiration = None
consume_forever = True

# start consuming
msg_proc.consume_queue(queue=queue,
                       heartbeat=heartbeat,
                       expiration=expiration,
                       sub_serializer=serializer,
                       pub_serializer=pub_serializer,
                       seconds_to_consume=seconds_to_consume,
                       forever=consume_forever,
                       # Optional: if you're chaining a publish hook to another system
                       exchange=exchange,
                       # Optional: if you're chaining a publish hook to another system
                       routing_key=routing_key,
                       # Pass in a custom callback
                       # for processing messages found in the queue
                       callback=relay_callback)

log.info("End - {}".format(name))
