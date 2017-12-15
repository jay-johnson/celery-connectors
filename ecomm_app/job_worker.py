#!/usr/bin/env python

import os
import logging
# import the app's tasks
import ecomm_app.ecommerce.tasks

name = "ecommerce-worker"

log = logging.getLogger(name)

log.info("Start - {}".format(name))

default_broker_url = "pyamqp://rabbitmq:rabbitmq@localhost:5672//"
default_backend_url = "redis://localhost:6379/10"
default_config_module = "ecomm_app.ecommerce.celeryconfig_pub_sub"

worker_broker_url = os.getenv("WORKER_BROKER_URL",
                              default_broker_url).strip().lstrip()

ssl_options = {}
transport_options = {}

# Get the Celery app from the ecommerce project's get_celery_app
app = ecomm_app.ecommerce.tasks.get_celery_app(
          name=name,
          auth_url=worker_broker_url,
          backend_url=default_backend_url)

# if you want to discover tasks in other directories:
# app.autodiscover_tasks(["some_dir_name_with_tasks"])

log.info("End - {}".format(name))
