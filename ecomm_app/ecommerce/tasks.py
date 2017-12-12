import os
import time
import logging
from celery import Celery
from celery.task import task

log = logging.getLogger("worker")


def ev(k, v):
    return os.getenv(k, v).strip().lstrip()
# end of ev


def get_celery_app(name=ev(
                       "CELERY_NAME",
                       "relay"),
                   auth_url=ev(
                       "BROKER_URL",
                       "amqp://rabbitmq:rabbitmq@localhost:5672//"),
                   ssl_options={},
                   transport_options={},
                   path_to_config_module="ecomm_app.ecommerce.celeryconfig_pub_sub",
                   worker_log_format="relay - %(asctime)s: %(levelname)s %(message)s",
                   **kwargs):

    # get the Celery application
    app = Celery(name,
                 broker=auth_url)

    app.config_from_object(path_to_config_module,
                           namespace="CELERY")

    app.conf.update(kwargs)

    if len(transport_options) > 0:
        log.info(("loading transport_options={}")
                 .format(transport_options))
        app.conf.update(**transport_options)
    # custom tranport options

    if len(ssl_options) > 0:
        log.info(("loading ssl_options={}")
                 .format(ssl_options))
        app.conf.update(**ssl_options)
    # custom ssl options

    return app
# end of get_celery_app


@task(queue="handle_user_conversion_events")
def handle_user_conversion_events(body={},
                                  msg={}):

    label = "user_conversion_events"

    log.info(("task - {} - start "
              "body={}")
             .format(label,
                     body))

    if "simulate_processing_lag" in body:
        log.info(("task - {} - simulating processing"
                  "lag={} sleeping")
                 .format(label,
                         body["simulate_processing_lag"]))
        time.sleep(float(body["simulate_processing_lag"]))
    # end of handling adding artifical lag for testing Celery

    log.info(("task - {} - done")
             .format(label))

    return True
# end of handle_user_conversion_events
