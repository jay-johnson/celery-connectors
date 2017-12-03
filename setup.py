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


cur_path, cur_script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(cur_path))

install_requires = [
    "pep8>=1.7.1",
    "flake8>=3.4.1",
    "redis",
    "celery>=4.1.0",
    "kombu>=4.1.0",
    "logstash-formatter",
    "python-logstash",
    "docker-compose",
    "coverage",
    "future",
    "pylint",
    "unittest2",
    "mock"
]


if sys.version_info < (2, 7):
    warnings.warn(
        "Python 2.6 is no longer officially supported by RedTen. "
        "If you have any questions, please file an issue on Github or "
        "contact us at https://github.com/jay-johnson/sci-pype",
        DeprecationWarning)


def celery_connectors_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="test_*.py")
    return test_suite


# Don"t import celery_connectors module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "celery_connectors"))

setup(
    name="celery-connectors",
    cmdclass={"build_py": build_py},
    version="1.0.4",
    description="Celery Headless Connectors",
    long_description="Running headless Celery bootsteps to process " +
    "json or pickled messages from Redis, RabbitMQ or AWS SQS. " +
    "Also has a Kombu Publisher with docker RabbitMQ and Redis " +
    "containers  included as well. Headless means no task " +
    "result backend (like mongo). I am planning to glue Django " +
    "and Jupyter together with this connection framework, and " +
    "allow workers to process messages from my windows laptop " +
    "out of a shared broker.",
    author="Jay Johnson",
    author_email="jay.p.h.johnson@gmail.com",
    url="https://github.com/jay-johnson/celery-connectors",
    packages=[
        "celery_connectors",
        "celery_connectors.redis",
        "celery_connectors.logging"
    ],
    package_data={},
    install_requires=install_requires,
    test_suite="setup.celery_connectors_test_suite",
    tests_require=[
    ],
    scripts=[
        "./celery_connectors/redis/redis-subscribe-and-read-messages.py",
        "./celery_connectors/redis/redis-publish-messages.py",
        "./celery_connectors/rabbitmq/rabbitmqadmin.py",
        "./celery_connectors/rabbitmq/list-queues.sh",
        "./celery_connectors/rabbitmq/list-exchanges.sh",
        "./celery_connectors/scripts/subscribe-to-rabbitmq.sh",
        "./celery_connectors/scripts/subscribe-to-redis.sh",
        "./start-redis-and-rabbitmq.sh",
        "./stop-redis-and-rabbitmq.sh"
    ],
    use_2to3=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
