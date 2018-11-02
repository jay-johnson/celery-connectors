import os
import sys
import warnings
import unittest

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

"""
https://packaging.python.org/guides/making-a-pypi-friendly-readme/
check the README.rst works on pypi as the
long_description with:
twine check dist/*
"""
long_description = open('README.rst').read()

cur_path, cur_script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(cur_path))

install_requires = [
    'ansible>=1.9',
    'pep8>=1.7.1',
    'flake8>=3.4.1',
    'boto3',
    'pycurl',
    'redis',
    'celery>=4.1.0',
    'kombu>=4.1.0',
    'logstash-formatter',
    'python-logstash',
    'coverage',
    'future',
    'pylint',
    'spylunking',
    'unittest2',
    'mock'
]


if sys.version_info < (2, 7):
    warnings.warn(
        'Python 2.6 is not supported.',
        DeprecationWarning)


def celery_connectors_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


# Don't import celery_connectors module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'celery_connectors'))

setup(
    name='celery-connectors',
    cmdclass={'build_py': build_py},
    version='1.0.30',
    description='Celery Connectors',
    long_description=long_description,
    author='Jay Johnson',
    author_email='jay.p.h.johnson@gmail.com',
    url='https://github.com/jay-johnson/celery-connectors',
    packages=[
        'celery_connectors',
        'celery_connectors.redis',
        'celery_connectors.log'
    ],
    package_data={},
    install_requires=install_requires,
    test_suite='setup.celery_connectors_test_suite',
    tests_require=[
    ],
    scripts=[
        './celery_connectors/redis/redis-subscribe-and-read-messages.py',
        './celery_connectors/redis/redis-publish-messages.py',
        './celery_connectors/rabbitmq/rabbitmqadmin.py',
        './celery_connectors/rabbitmq/list-bindings.sh',
        './celery_connectors/rabbitmq/list-channels.sh',
        './celery_connectors/rabbitmq/list-connections.sh',
        './celery_connectors/rabbitmq/list-consumers.sh',
        './celery_connectors/rabbitmq/list-exchanges.sh',
        './celery_connectors/rabbitmq/list-queues.sh',
        './celery_connectors/rabbitmq/rmq-close-all-connections.sh',
        './celery_connectors/rabbitmq/rmq-trace-on.sh',
        './celery_connectors/rabbitmq/rmq-trace-off.sh',
        './celery_connectors/rabbitmq/rmq-status.sh',
        './celery_connectors/rabbitmq/watch-queues.sh',
        './celery_connectors/scripts/subscribe-to-rabbitmq.sh',
        './celery_connectors/scripts/subscribe-to-redis.sh',
        './publish-user-conversion-events-redis.py',
        './publish-user-conversion-events-rabbitmq.py',
        './start-kombu-message-processor-redis.py',
        './start-kombu-message-processor-rabbitmq.py',
        './start-mixin-json-relay.py',
        './start-mixin-celery-relay.py',
        './start-mixin-publisher.py',
        './start-mixin-load-test.py',
        './start-load-test-rabbitmq.py',
        './start-subscriptions-rabbitmq-test.py',
        './start-load-test-redis.py',
        './run_rabbitmq_publisher.py',
        './run_redis_publisher.py',
        './kombu_rabbitmq_subscriber.py',
        './kombu_redis_subscriber.py',
        './kombu_sqs_publisher.py',
        './kombu_sqs_subscriber.py',
        './kombu_mixin_subscriber.py',
        './start-redis-and-rabbitmq.sh',
        './stop-redis-and-rabbitmq.sh',
        './start-persistence-containers.sh',
        './start-ecomm-relay.py'
    ],
    use_2to3=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
