#!/bin/bash

path_to_worker_module="ecomm_app.job_worker"
worker_name="ecommerce_subscriber"
num_workers=3
log_level="INFO"

# http://docs.celeryproject.org/en/latest/userguide/optimizing.html
celery worker -A ${path_to_worker_module} --loglevel=${log_level} -n ${worker_name} -c ${num_workers} -Ofair
