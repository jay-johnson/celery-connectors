#!/bin/bash

path_to_worker_module="ecomm_app.job_worker"
worker_name="ecommerce_subscriber"
num_workers=3
log_level="INFO"
path_to_celery="celery"

if [[ "${PATH_TO_WORKER_MODULE}" != "" ]]; then
    path_to_worker_module="${PATH_TO_WORKER_MODULE}"
fi
if [[ "${APP_NAME}" != "" ]]; then
    worker_name="${APP_NAME}"
fi
if [[ "${NUM_WORKERS}" != "" ]]; then
    num_workers=${NUM_WORKERS}
fi
if [[ "${LOG_LEVEL}" != "" ]]; then
    log_level="${LOG_LEVEL}"
fi
if [[ "${PATH_TO_CELERY}" != "" ]]; then
    path_to_celery="${PATH_TO_CELERY}"
fi

# http://docs.celeryproject.org/en/latest/userguide/optimizing.html
echo "${path_to_celery} worker -A ${path_to_worker_module} --loglevel=${log_level} -n ${worker_name} -c ${num_workers} -Ofair"
${path_to_celery} worker -A ${path_to_worker_module} --loglevel=${log_level} -n ${worker_name} -c ${num_workers} -Ofair
