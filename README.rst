Celery Headless Connectors
==========================

Celery_ is a great framework for processing messages in a backend message queue service like SQS, Redis or RabbitMQ. If you have a queue system with json/pickled messages, and if you do not want to track the internal celery task results, then hopefully this repository will help you out.

.. _Celery: http://docs.celeryproject.org/en/latest/

Why do I care?
--------------

- Do you want to read json or pickled messages out of a queue and have a framework handle the scaling and deployment aspects all out of the box? 

- Do you want a simple way to read out of queues without setting up a task result backend (mongo)?

- Do you want to connect a windows python client to a backend linux system or cluster?

- Do you want to communicate with all your AWS VPC backends over SQS?

- Do you want to glue python and non-python technologies together through a message queue backend?

- Do you want something that works with python 2 and 3?

How do I get started?
-------------------

#.  Setup the virtualenv 

    If you want to use python 2:

    ::

        virtualenv venv && source venv/bin/activate && pip install celery-connectors

    If you want to use python 3:

    ::

        virtualenv -p python3 venv && source venv/bin/activate && pip install celery-connectors

#.  Confirm the pip is installed

    ::

        pip list | grep celery-connectors

#.  Start the containers

    ::

        start-redis-and-rabbitmq.sh

#.  Check the Redis and RabbitMQ containers are running

    ::

        $ docker ps
        CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS                                                                                                       NAMES
        68f3b6e71563        redis:4.0.5-alpine          "docker-entrypoint..."   34 seconds ago      Up 33 seconds       0.0.0.0:6379->6379/tcp, 0.0.0.0:16379->16379/tcp                                                            celredis1
        3fd938f4d5e0        rabbitmq:3.6.6-management   "docker-entrypoint..."   23 hours ago        Up 33 seconds       4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp, 15671/tcp, 0.0.0.0:25672->25672/tcp   celrabbit1
        $ 

    
Redis Message Processing Example
--------------------------------

This example uses Celery bootsteps (http://docs.celeryproject.org/en/latest/userguide/extending.html) to run a standalone, headless subscriber that consumes messages from a Redis key which emulates a RabbitMQ queue. Kombu publishes the message to the Redis key.

#.  Publish a message

    ::

        $ ./run_redis_publisher.py
        2017-12-03 00:41:21,323 - run-redis-publisher - INFO - Start - run-redis-publisher
        2017-12-03 00:41:21,353 - run-redis-publisher - INFO - Building message
        2017-12-03 00:41:21,353 - run-redis-publisher - INFO - Sending msg={'account_id': 123} ex=Exchange reporting.accounts(direct) rk=reporting.accounts
        2017-12-03 00:41:21,355 - run-redis-publisher - INFO - End - run-redis-publisher
        $

#.  Consume messages using the subscriber module

    ::

        celery worker -A run_redis_subscriber --loglevel=DEBUG

#.  Run the publisher module again and watch the celery log

    ::

        [2017-12-03 00:42:11,184: INFO/MainProcess] recv msg props=<Message object at 0x7fbb01c81048 with details {'properties': {}, 'state': 'RECEIVED', 'delivery_info': {'routing_key': 'reporting.accounts', 'exchange': 'reporting.accounts'}, 'body_length': 19, 'delivery_tag': 'e96600be-d9de-42d7-a9cd-729b475a6a92', 'content_type': 'application/json'}> body={'account_id': 123}
        [2017-12-03 00:42:11,186: INFO/MainProcess] recv msg props=<Message object at 0x7fbb01c810d8 with details {'properties': {}, 'state': 'RECEIVED', 'delivery_info': {'routing_key': 'reporting.accounts', 'exchange': 'reporting.accounts'}, 'body_length': 19, 'delivery_tag': '8958339d-4324-4af5-b77e-241d41f5ddf3', 'content_type': 'application/json'}> body={'account_id': 123}
        [2017-12-03 00:42:21,019: INFO/MainProcess] recv msg props=<Message object at 0x7fbb01c81168 with details {'properties': {}, 'state': 'RECEIVED', 'delivery_info': {'routing_key': 'reporting.accounts', 'exchange': 'reporting.accounts'}, 'body_length': 19, 'delivery_tag': '5204aa96-788c-472d-835c-ab66bfe1e0da', 'content_type': 'application/json'}> body={'account_id': 123}
        [2017-12-03 00:42:22,675: INFO/MainProcess] recv msg props=<Message object at 0x7fbb01c810d8 with details {'properties': {}, 'state': 'RECEIVED', 'delivery_info': {'routing_key': 'reporting.accounts', 'exchange': 'reporting.accounts'}, 'body_length': 19, 'delivery_tag': 'e065c120-ada0-458b-b024-18c28a36172b', 'content_type': 'application/json'}> body={'account_id': 123}

#.  Look at the Redis keys

    ::

        $ redis-cli
        127.0.0.1:6379> keys *
        1) "_kombu.binding.reporting.accounts"
        2) "_kombu.binding.celery.pidbox"
        3) "unacked_mutex"
        4) "_kombu.binding.celery"
        5) "_kombu.binding.celeryev"
        127.0.0.1:6379> 
        $ 


RabbitMQ Message Processing Example
-----------------------------------

This example uses Celery bootsteps (http://docs.celeryproject.org/en/latest/userguide/extending.html) to run a standalone, headless subscriber that consumes routed messages. It will set up a RabbitMQ topic exchange with a queue that is bound using a routing key. Once the entities are available in RabbitMQ, Kombu publishes the message to the Exchange and RabbitMQ provides the messaging facility to route the messages to the subscribed celery workers' Queue.

#.  Publish a message

    ::

        $ ./run_rabbitmq_publisher.py
        2017-12-03 00:45:02,783 - run-rabbitmq-publisher - INFO - Start - run-rabbitmq-publisher
        2017-12-03 00:45:02,800 - amqp - DEBUG - Start from server, version: 0.9, properties: {'product': 'RabbitMQ', 'cluster_name': 'rabbit@rabbit1', 'platform': 'Erlang/OTP', 'copyright': 'Copyright (C) 2007-2016 Pivotal Software, Inc.', 'information': 'Licensed under the MPL.  See http://www.rabbitmq.com/', 'capabilities': {'direct_reply_to': True, 'connection.blocked': True, 'per_consumer_qos': True, 'exchange_exchange_bindings': True, 'publisher_confirms': True, 'consumer_cancel_notify': True, 'authentication_failure_close': True, 'consumer_priorities': True, 'basic.nack': True}, 'version': '3.6.6'}, mechanisms: [b'AMQPLAIN', b'PLAIN'], locales: ['en_US']
        2017-12-03 00:45:02,803 - amqp - DEBUG - using channel_id: 1
        2017-12-03 00:45:02,806 - amqp - DEBUG - Channel open
        2017-12-03 00:45:02,807 - amqp - DEBUG - using channel_id: 2
        2017-12-03 00:45:02,813 - amqp - DEBUG - Channel open
        2017-12-03 00:45:02,816 - run-rabbitmq-publisher - INFO - Building message
        2017-12-03 00:45:02,816 - run-rabbitmq-publisher - INFO - Sending msg={'account_id': 123} ex=Exchange reporting(topic) rk=reporting.accounts
        2017-12-03 00:45:02,818 - run-rabbitmq-publisher - INFO - End - run-rabbitmq-publisher
        $

#.  Confirm the message is ready in the RabbitMQ queue

    Note the ``messages`` and ``messages_ready`` count increased while the ``messages_unacknowledged`` did not. Which is because we have not started the subscriber to process ready messages in the ``reporting.accounts`` queue.

    ::

        $ list-queues.sh

        Listing Queues broker=localhost:15672
        +--------------------+-----------+----------+----------------+-------------------------+
        |        name        | consumers | messages | messages_ready | messages_unacknowledged |
        +--------------------+-----------+----------+----------------+-------------------------+
        | celery             | 0         | 0        | 0              | 0                       |
        | reporting.accounts | 0         | 1        | 1              | 0                       |
        +--------------------+-----------+----------+----------------+-------------------------+

#.  Consume that message by starting up the producer celery module

    ::

        celery worker -A run_rabbitmq_subscriber --loglevel=DEBUG

#.  Confirm the worker's logs show the message was received (recv)

    ::

        [2017-12-03 00:46:38,565: INFO/MainProcess] recv msg props=<Message object at 0x7fdc75c37dc8 with details {'content_type': 'application/json', 'properties': {}, 'state': 'RECEIVED', 'body_length': 19, 'delivery_info': {'routing_key': 'reporting.accounts', 'exchange': 'reporting'}, 'delivery_tag': 1}> body={'account_id': 123}
        [2017-12-03 00:46:38,565: INFO/MainProcess] celery@localhost.localdomain ready.

#.  Verify the message is no longer in the queue

    ::

        $ list-queues.sh

        Listing Queues broker=localhost:15672
        +-----------------------------------------------+-----------+----------+----------------+-------------------------+
        |                     name                      | consumers | messages | messages_ready | messages_unacknowledged |
        +-----------------------------------------------+-----------+----------+----------------+-------------------------+
        | celery                                        | 1         | 0        | 0              | 0                       |
        | celery@localhost.localdomain.celery.pidbox    | 1         | 0        | 0              | 0                       |
        | celeryev.935809b9-526a-4d48-a0f9-b8f5c675dbec | 1         | 0        | 0              | 0                       |
        | reporting.accounts                            | 1         | 0        | 0              | 0                       |
        +-----------------------------------------------+-----------+----------+----------------+-------------------------+

Redis Kombu Subscriber
======================

If you do not want to use Celery, you can use the ``KombuSubscriber`` class to process messages. This class will wait for a configurable amount of seconds to consume a single message from the subscribed queue and then stop processing.

#.  Run the Redis Publisher

    ::

        $ ./run_redis_publisher.py 
        2017-12-03 17:26:12,896 - run-redis-publisher - INFO - Start - run-redis-publisher
        2017-12-03 17:26:12,896 - run-redis-publisher - INFO - Building message
        2017-12-03 17:26:12,896 - run-redis-publisher - INFO - Sending msg={'account_id': 123} ex=reporting.accounts rk=reporting.accounts
        2017-12-03 17:26:12,924 - redis-publisher - INFO - READY - PUB - exch=reporting.accounts queue=<Queue reporting.accounts -> <Exchange reporting.accounts(topic) bound to chan:2> -> reporting.accounts bound to chan:2> body={'account_id': 123}
        2017-12-03 17:26:12,927 - run-redis-publisher - INFO - End - run-redis-publisher
        $

#.  Run the Redis Kombu Subscriber

    By default, this will wait for a single message message to be delivered within 10 seconds.

    ::

        $ ./kombu_redis_subscriber.py 
        2017-12-03 17:26:08,854 - kombu-redis-subscriber - INFO - Start - kombu-redis-subscriber
        2017-12-03 17:26:08,884 - kombu-redis-subscriber - INFO - kombu-redis-subscriber - kombu.subscriber queues=reporting.accounts wait=10.0 callback=<function handle_message at 0x7f70762c7950>
        2017-12-03 17:26:12,927 - kombu-redis-subscriber - INFO - kombu.subscriber recv msg props=<Message object at 0x7f7068151af8 with details {'state': 'RECEIVED', 'delivery_info': {'exchange': 'reporting.accounts', 'routing_key': 'reporting.accounts'}, 'delivery_tag': '0108f196-71e6-4511-86eb-945e46e0c5ed', 'body_length': 19, 'properties': {}, 'content_type': 'application/json'}> body={'account_id': 123}
        2017-12-03 17:26:12,928 - kombu-redis-subscriber - INFO - End - kombu-redis-subscriber
        $


RabbitMQ Kombu Subscriber
=========================

If you do not want to use Celery, you can use the ``KombuSubscriber`` class to process messages. This class will wait for a configurable amount of seconds to consume a single message from the subscribed queue and then stop processing.

#.  Run the RabbitMQ Subscriber

    Please note this output assumes there are no messages in the queue already from a previous test

    ::

        $ ./kombu_rabbitmq_subscriber.py 
        2017-12-03 17:23:09,067 - kombu-rabbitmq-subscriber - INFO - Start - kombu-rabbitmq-subscriber
        2017-12-03 17:23:09,091 - kombu-rabbitmq-subscriber - INFO - kombu-rabbitmq-subscriber - kombu.subscriber queues=reporting.accounts wait=10.0 callback=<function handle_message at 0x7f50f8599950>
        2017-12-03 17:23:19,115 - kombu-rabbitmq-subscriber - INFO - End - kombu-rabbitmq-subscriber
        $

#.  Run the RabbitMQ Publisher

    ::

        $ ./run_rabbitmq_publisher.py 
        2017-12-03 17:23:24,026 - run-rabbitmq-publisher - INFO - Start - run-rabbitmq-publisher
        2017-12-03 17:23:24,028 - run-rabbitmq-publisher - INFO - Building message
        2017-12-03 17:23:24,028 - run-rabbitmq-publisher - INFO - Sending msg={'account_id': 123} ex=reporting rk=reporting.accounts
        2017-12-03 17:23:24,047 - rabbitmq-publisher - INFO - READY - PUB - exch=reporting queue=<Queue reporting.accounts -> <Exchange reporting(topic) bound to chan:2> -> reporting.accounts bound to chan:2> body={'account_id': 123}
        2017-12-03 17:23:24,048 - run-rabbitmq-publisher - INFO - End - run-rabbitmq-publisher
        $

#.  Run the RabbitMQ Kombu Subscriber

    By default, this will wait for a single message to be delivered within 10 seconds.

    ::

        $ ./kombu_rabbitmq_subscriber.py 
        2017-12-03 17:23:22,132 - kombu-rabbitmq-subscriber - INFO - Start - kombu-rabbitmq-subscriber
        2017-12-03 17:23:22,157 - kombu-rabbitmq-subscriber - INFO - kombu-rabbitmq-subscriber - kombu.subscriber queues=reporting.accounts wait=10.0 callback=<function handle_message at 0x7f1a5d4c4950>
        2017-12-03 17:23:24,049 - kombu-rabbitmq-subscriber - INFO - kombu.subscriber recv msg props=<Message object at 0x7f1a4f602708 with details {'state': 'RECEIVED', 'content_type': 'application/json', 'delivery_info': {'exchange': 'reporting', 'routing_key': 'reporting.accounts'}, 'body_length': 19, 'delivery_tag': 1, 'properties': {}}> body={'account_id': 123}
        2017-12-03 17:23:24,049 - kombu-rabbitmq-subscriber - INFO - End - kombu-rabbitmq-subscriber
        $

Debugging with rabbitmqadmin
=============================

The pip and development build will install ``rabbitmqadmin`` (https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.0/bin/rabbitmqadmin) version 3.7.0. It is a great utility for verifying RabbitMQ messaging and does not require having access to the RabbitMQ cluster's host nodes (or a machine with rabbitmqctl on it).

Please note: ``rabbitmqadmin`` uses the management HTTP port (not the amqp port 5672) which requires a broker to have the management plugin enabled to work if you're using this with an external RabbitMQ cluster.

Checking queues
---------------

Script in pip

::

    $ ./list-queues.sh 

    Listing Queues broker=localhost:15672
    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery             | 0         | 0        | 0              | 0                       |
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

Manual way

::

    $ rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list queues
    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery             | 0         | 0        | 0              | 0                       |
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+
    $ 

Checking exchanges
------------------

Script in pip

::

    $ ./list-exchanges.sh 

    Listing Exchanges broker=localhost:15672
    +---------------------+---------+
    |        name         |  type   |
    +---------------------+---------+
    |                     | direct  |
    | amq.direct          | direct  |
    | amq.fanout          | fanout  |
    | amq.headers         | headers |
    | amq.match           | headers |
    | amq.rabbitmq.log    | topic   |
    | amq.rabbitmq.trace  | topic   |
    | amq.topic           | topic   |
    | celery              | direct  |
    | celery.pidbox       | fanout  |
    | celeryev            | topic   |
    | reply.celery.pidbox | direct  |
    | reporting.accounts  | topic   |
    +---------------------+---------+

Manual way

::

    $ rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list exchanges name typa
    +---------------------+---------+
    |        name         |  type   |
    +---------------------+---------+
    |                     | direct  |
    | amq.direct          | direct  |
    | amq.fanout          | fanout  |
    | amq.headers         | headers |
    | amq.match           | headers |
    | amq.rabbitmq.log    | topic   |
    | amq.rabbitmq.trace  | topic   |
    | amq.topic           | topic   |
    | celery              | direct  |
    | celery.pidbox       | fanout  |
    | celeryev            | topic   |
    | reply.celery.pidbox | direct  |
    | reporting.accounts  | topic   |
    +---------------------+---------+
    $ 

List Bindings
=============

Script in pip

::

    $ list-bindings.sh 

    Listing Bindings broker=localhost:15672
    +--------------------+--------------------+--------------------+
    |       source       |    destination     |    routing_key     |
    +--------------------+--------------------+--------------------+
    |                    | celery             | celery             |
    |                    | reporting.accounts | reporting.accounts |
    | celery             | celery             | celery             |
    | reporting          | reporting.accounts | reporting.accounts |
    +--------------------+--------------------+--------------------+

Manual way

::

    $ rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list bindings source destination routing_key
    +--------------------+--------------------+--------------------+
    |       source       |    destination     |    routing_key     |
    +--------------------+--------------------+--------------------+
    |                    | celery             | celery             |
    |                    | reporting.accounts | reporting.accounts |
    | celery             | celery             | celery             |
    | reporting          | reporting.accounts | reporting.accounts |
    +--------------------+--------------------+--------------------+


Development Guide
=================

#.  Install the development environment

    ::

        virtualenv -p python3 venv && source venv/bin/activate && python setup.py develop

#.  Run tests

    ::

        python setup.py test

Linting
-------

::

    pycodestyle --max-line-length=160 --exclude=venv,build,.tox,celery_connectors/rabbitmq/rabbitmqadmin.py

License
-------

Apache 2.0 - Please refer to the LICENSE for more details
