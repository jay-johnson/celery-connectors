#!/bin/bash

path_to_worker_module="ecomm_app.job_worker"
worker_name="ecommerce_subscriber"
celery worker -A ${path_to_worker_module} --loglevel=INFO -n ${worker_name}
