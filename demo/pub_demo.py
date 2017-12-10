#!/usr/bin/env python

import logging
import uuid
from datetime import datetime
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.utils import ev
import ecommerce.tasks

setup_logging()

name = "demo-celery-publisher"

log = logging.getLogger(name)

pub_auth_url = ev("PUB_BROKER_URL",
                  "amqp://rabbitmq:rabbitmq@localhost:5672//")

app = ecommerce.tasks.get_celery_app(name="demo",
                                     auth_url=pub_auth_url)

task_name = "ecommerce.tasks.handle_user_conversion_events"
now = datetime.now().isoformat()
body = {"account_id": 999,
        "subscription_id": 321,
        "stripe_id": 876,
        "created": now,
        "product_id": "JJJ",
        "version": 1,
        "msg_id": uuid.uuid4()}

msg = {"internals": True}

log.info(("Sending broker={} "
          "body={}")
         .format(app.conf.broker_url,
                 body))

app.send_task(task_name, (body, msg))
