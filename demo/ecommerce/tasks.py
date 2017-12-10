import os
import logging
from celery import Celery
from celery.task import task
from celery_connectors.utils import ev

log = logging.getLogger("worker")


def get_celery_app(name=ev(
                       "CELERY_NAME",
                       "relay"),
                   auth_url=ev(
                       "BROKER_URL",
                       "amqp://rabbitmq:rabbitmq@localhost:5672//"),
                   ssl_options={},
                   transport_options={},
                   worker_log_format="relay - %(asctime)s: %(levelname)s %(message)s",
                   **kwargs):

    # get the Celery application
    app = Celery(name, broker=auth_url)

    app.config_from_object("pub_sub_demo", namespace="CELERY")

    app.conf.update(kwargs)

    return app
# end of get_celery_app


@task(queue="handle_user_conversion_events")
def handle_user_conversion_events(body={},
                                  msg={}):

    label = "uce"

    log.info(("Handle - {} - start "
              "body={}")
             .format(label,
                     body))

    log.info(("Handle - {} - done")
             .format(label))

    return True
# end of handle_user_conversion_events
