#!/usr/bin/env python

import os
import logging
from celery import Celery
from celery.task import task
from celery_connectors.utils import ev
from celery_connectors.log.setup_logging import setup_logging
from celery_connectors.message_processor import MessageProcessor
import ecommerce.tasks

setup_logging()

name = "msg-proc"

log = logging.getLogger("loader-name")

log.info("Start - {}".format(name))

sub_auth_url = ev("SUB_BROKER_URL",
                  "amqp://rabbitmq:rabbitmq@localhost:5672//")

ssl_options = {}
transport_options = {}

# Get the Celery app from the ecommerce project's get
app = ecommerce.tasks.get_celery_app(name="demo",
                                     auth_url=sub_auth_url)

# if you want to discover tasks in other directories:
# app.autodiscover_tasks(["example"])

body = {}
msg = {"source": "rabbitmq",
       "data": {}}

log.info("End - {}".format(name))
