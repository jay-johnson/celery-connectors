Celery Headless Connectors
==========================

Celery_ is a great framework for processing messages in a backend message queue service like Redis or RabbitMQ. If you have a queue system with json/pickled messages, and if you do not want to track the internal celery task results, then hopefully this repository will help you out.

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

        docker ps
        CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS                                                                                                       NAMES
        913e8092dbde        mher/flower:latest          "/usr/local/bin/py..."   35 seconds ago      Up 35 seconds                                                                                                                   celflowerredis
        b6983a1316ba        rabbitmq:3.6.6-management   "docker-entrypoint..."   35 seconds ago      Up 34 seconds       4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp, 15671/tcp, 0.0.0.0:25672->25672/tcp   celrabbit1
        52cb4c511d61        redis:4.0.5-alpine          "docker-entrypoint..."   35 seconds ago      Up 34 seconds       0.0.0.0:6379->6379/tcp, 0.0.0.0:16379->16379/tcp                                                            celredis1
        202bdaf70784        mher/flower:latest          "/usr/local/bin/py..."   35 seconds ago      Up 35 seconds                                                                                                                   celflowerrabbit

Running an Ecommerce JSON-to-Celery Relay Service
=================================================

This will simulate hooking up an existing Celery application to start processing Celery tasks from JSON messages in a RabbitMQ queue. This is useful because it allows reusing existing Celery application tasks over a JSON messaging layer for mapping payloads to specific, existing Celery tasks. With this approach you can glue python and non-python services together provided that they can publish JSON messages to Redis, RabbitMQ or AWS SQS (please refer to the `fix SQS`_ section). Each of the components below can scale horizontally for redundancy. Each one also utilizes native RabbitMQ acks (https://www.rabbitmq.com/confirms.html) to ensure messages are never deleted or lost until propagation to the next queue or component has been confirmed.

.. _fix SQS: https://github.com/jay-johnson/celery-connectors#temporary-fix-for-kombu-sqs

Note: Please run this demo with three separate terminal sessions and a browser to view the Celery application's task progress in Flower.

Start Ecommerce Celery Worker
-----------------------------

Start a Celery worker for an existing ecommerce application from a hypothetical Django or Flask server.

Note: Please run this from the base directory for the repository and source the virtual env: ``source venv/bin/activate``

::

    ./start-ecomm-worker.sh 
    
    -------------- celery@ecommerce_subscriber v4.1.0 (latentcall)
    ---- **** ----- 
    --- * ***  * -- Linux-4.7.4-200.fc24.x86_64-x86_64-with-fedora-24-Twenty_Four 2017-12-10 14:31:37
    -- * - **** --- 
    - ** ---------- [config]
    - ** ---------- .> app:         ecommerce-worker:0x7f61a973d470
    - ** ---------- .> transport:   amqp://rabbitmq:**@localhost:5672//
    - ** ---------- .> results:     rpc://
    - *** --- * --- .> concurrency: 4 (prefork)
    -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
    --- ***** ----- 
    -------------- [queues]
                    .> celery           exchange=celery(direct) key=celery
                    

    [tasks]
    . ecomm_app.ecommerce.tasks.handle_user_conversion_events

    [2017-12-10 14:31:37,165: INFO/MainProcess] Connected to amqp://rabbitmq:**@127.0.0.1:5672//
    [2017-12-10 14:31:37,182: INFO/MainProcess] mingle: searching for neighbors
    [2017-12-10 14:31:38,217: INFO/MainProcess] mingle: all alone
    [2017-12-10 14:31:38,262: INFO/MainProcess] celery@ecommerce_subscriber ready.
    [2017-12-10 14:31:41,014: INFO/MainProcess] Events of group {task} enabled by remote.

Notice the worker is named ``celery@ecommerce_subscriber`` this is the identifier for viewing the Celery application in Flower:

http://localhost:5555/worker/celery@ecommerce_subscriber (login: admin/admin)

Start Ecomm Relay
-----------------

This process will consume JSON dictionary messages on the ``user.events.conversions`` RabbitMQ queue and pass the message to the ecomm Celery app as a ``ecomm_app.ecommerce.tasks.handle_user_conversion_events`` Celery task.

Please start this in a new terminal that has sourced the virtual env: ``source venv/bin/activate``

::

    ./start-ecomm-relay.py 
    2017-12-10 14:34:20,290 - ecomm-relay-loader - INFO - Start - ecomm-relay
    2017-12-10 14:34:20,290 - message-processor - INFO - ecomm-relay START - consume_queue=user.events.conversions rk=reporting.accounts callback=relay_callback
    2017-12-10 14:34:20,290 - kombu-subscriber - INFO - setup routing
    2017-12-10 14:34:20,314 - kombu-subscriber - INFO - msg-sub - kombu.subscriber queues=user.events.conversions consuming with callback=relay_callback

Publish a User Conversion Event to the Ecomm Relay
--------------------------------------------------

This will use Kombu to publish a JSON dictionary message to the ``user.events.conversions`` RabbitMQ queue which is monitored by the ecomm relay.

Please start this in a new terminal that has sourced the virtual env: ``source venv/bin/activate``

::

    publish-user-conversion-events-rabbitmq.py 
    INFO:publish-user-conversion-events:Start - publish-user-conversion-events
    INFO:publish-user-conversion-events:Sending user conversion event msg={'account_id': 777, 'product_id': 'XYZ', 'stripe_id': 999, 'created': '2017-12-10T14:40:54.733901', 'subscription_id': 888} ex=user.events rk=user.events.conversions
    INFO:kombu-publisher:SEND - exch=user.events rk=user.events.conversions
    INFO:publish-user-conversion-events:End - publish-user-conversion-events sent=True

Verify the Ecomm Relay Processed the Conversion Message
-------------------------------------------------------

The logs for the ecomm relay should show something similar to:

::

    2017-12-10 14:40:54,774 - ecomm-relay-loader - INFO - Sending broker=amqp://rabbitmq:rabbitmq@localhost:5672// body={'msg_id': '3b2aa0e0-2b68-421c-9a4f-3ad9a30a5abc', 'stripe_id': 876, 'subscription_id': 321, 'created': '2017-12-10T14:40:54.772966', 'version': 1, 'org_msg': {'created': '2017-12-10T14:40:54.733901', 'stripe_id': 999, 'subscription_id': 888, 'account_id': 777, 'product_id': 'XYZ'}, 'account_id': 999, 'product_id': 'JJJ'}
    2017-12-10 14:40:54,840 - ecomm-relay-loader - INFO - Done with msg_id=3b2aa0e0-2b68-421c-9a4f-3ad9a30a5abc result=True
    
Verify the Ecomm Celery Application Processed the Task
------------------------------------------------------

The logs for the ecomm Celery worker should show something similar to:

::

    [2017-12-10 14:40:54,815: INFO/MainProcess] Received task: ecomm_app.ecommerce.tasks.handle_user_conversion_events[737a1b0a-20f9-4ef5-ade8-d5f437e4fbb3]  
    [2017-12-10 14:40:54,817: INFO/ForkPoolWorker-3] task - user_conversion_events - start body={'account_id': 999, 'product_id': 'JJJ', 'org_msg': {'account_id': 777, 'product_id': 'XYZ', 'created': '2017-12-10T14:40:54.733901', 'subscription_id': 888, 'stripe_id': 999}, 'created': '2017-12-10T14:40:54.772966', 'stripe_id': 876, 'subscription_id': 321, 'msg_id': '3b2aa0e0-2b68-421c-9a4f-3ad9a30a5abc', 'version': 1}
    [2017-12-10 14:40:54,817: INFO/ForkPoolWorker-3] task - user_conversion_events - done
    [2017-12-10 14:40:54,839: INFO/ForkPoolWorker-3] Task ecomm_app.ecommerce.tasks.handle_user_conversion_events[737a1b0a-20f9-4ef5-ade8-d5f437e4fbb3] succeeded in 0.022475273000054585s: True

View the Ecomm Celery Worker Tasks in Flower
--------------------------------------------

The ``Processed`` and ``Succeeded`` task counts for the ``celery@ecommerce_subscriber`` should increment each time a User Conversion Event is published by the ecomm relay to the ecomm worker.

http://localhost:5555/dashboard

View specific task details:

http://localhost:5555/tasks

Stop the Ecomm Demo
-------------------

In the ecomm relay and ecomm worker terminal sessions use: ``ctrl + c`` to stop the processes.

Restart the docker containers to a good, clean state.

Stop:

::
    
    stop-redis-and-rabbitmq.sh 
    Stopping redis and rabbitmq
    Stopping celrabbit1      ... done
    Stopping celredis1       ... done
    Stopping celflowerredis  ... done
    Stopping celflowerrabbit ... done

Start:

::

    start-redis-and-rabbitmq.sh 
    Starting redis and rabbitmq
    Creating celrabbit1 ... done
    Creating celrabbit1 ... done
    Creating celredis1 ... done
    Creating celflowerredis ... done

Redis Message Processing Example
--------------------------------

This example uses Celery bootsteps (http://docs.celeryproject.org/en/latest/userguide/extending.html) to run a standalone, headless subscriber that consumes messages from a Redis key which emulates a RabbitMQ queue. Kombu publishes the message to the Redis key.

#.  Check that the Redis has no keys

    ::

        redis-cli
        127.0.0.1:6379> keys *
        (empty list or set)
        127.0.0.1:6379> 

#.  Publish a message

    ::

        run_redis_publisher.py 
        2017-12-09 08:20:04,026 - run-redis-publisher - INFO - Start - run-redis-publisher
        2017-12-09 08:20:04,027 - run-redis-publisher - INFO - Sending msg={'account_id': 123, 'created': '2017-12-09T08:20:04.027159'} ex=reporting.accounts rk=reporting.accounts
        2017-12-09 08:20:04,050 - redis-publisher - INFO - SEND - exch=reporting.accounts rk=reporting.accounts
        2017-12-09 08:20:04,052 - run-redis-publisher - INFO - End - run-redis-publisher sent=True

#.  Consume messages using the subscriber module

    ::

        celery worker -A run_redis_subscriber --loglevel=INFO

#.  Confirm the Celery worker received the message

    ::

        2017-12-09 08:20:08,221: INFO callback received msg body={u'account_id': 123, u'created': u'2017-12-09T08:20:04.027159'}

#.  View the Redis Subscriber in Flower

    Redis Flower server (login admin/admin)
    
    http://localhost:5556/

#.  Look at the Redis keys

    ::

        redis-cli
        127.0.0.1:6379> keys *
        1) "_kombu.binding.celeryev"
        2) "_kombu.binding.celery"
        3) "_kombu.binding.celery.pidbox"
        4) "_kombu.binding.reporting.accounts"
        5) "unacked_mutex"
        127.0.0.1:6379> 

RabbitMQ Message Processing Example
-----------------------------------

This example uses Celery bootsteps (http://docs.celeryproject.org/en/latest/userguide/extending.html) to run a standalone, headless subscriber that consumes routed messages. It will set up a RabbitMQ topic exchange with a queue that is bound using a routing key. Once the entities are available in RabbitMQ, Kombu publishes the message to the exchange and RabbitMQ provides the messaging facility to route the messages to the subscribed celery workers' queue.

#.  List the Queues

    ::

        list-queues.sh 

        Listing Queues broker=localhost:15672
        No items


#.  Publish a message

    ::

        run_rabbitmq_publisher.py 
        2017-12-09 11:00:54,419 - run-rabbitmq-publisher - INFO - Start - run-rabbitmq-publisher
        2017-12-09 11:00:54,419 - run-rabbitmq-publisher - INFO - Sending msg={'account_id': 456, 'created': '2017-12-09T11:00:54.419829'} ex=reporting rk=reporting.accounts
        2017-12-09 11:00:54,462 - rabbitmq-publisher - INFO - SEND - exch=reporting rk=reporting.accounts
        2017-12-09 11:00:54,463 - run-rabbitmq-publisher - INFO - End - run-rabbitmq-publisher sent=True

#.  Confirm the message is ready in the RabbitMQ Queue

    Note the ``messages`` and ``messages_ready`` count increased while the ``messages_unacknowledged`` did not. Which is because we have not started the subscriber to process ready messages in the ``reporting.accounts`` queue.

    ::

        list-queues.sh 

    Listing Queues broker=localhost:15672

    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | reporting.accounts | 0         | 1        | 1              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

#.  List the Exchanges

    ::

        list-exchanges.sh 

    Listing Exchanges broker=localhost:15672

    +--------------------+---------+
    |        name        |  type   |
    +--------------------+---------+
    |                    | direct  |
    +--------------------+---------+
    | amq.direct         | direct  |
    +--------------------+---------+
    | amq.fanout         | fanout  |
    +--------------------+---------+
    | amq.headers        | headers |
    +--------------------+---------+
    | amq.match          | headers |
    +--------------------+---------+
    | amq.rabbitmq.log   | topic   |
    +--------------------+---------+
    | amq.rabbitmq.trace | topic   |
    +--------------------+---------+
    | amq.topic          | topic   |
    +--------------------+---------+
    | reporting          | topic   |
    +--------------------+---------+

#.  Consume that message by starting up the producer celery module

    ::

        celery worker -A run_rabbitmq_subscriber --loglevel=INFO

#.  Confirm the worker's logs show the message was received

    ::

        2017-12-09 11:02:38,608: INFO callback received msg body={u'account_id': 456, u'created': u'2017-12-09T11:00:54.419829'}

#.  View the Rabbit Subscriber in Flower

    Rabbit Flower server (login admin/admin)
    
    http://localhost:5555/

#.  Verify the message is no longer in the Queue and Celery is connected as a consumer

    With the Celery RabbitMQ worker still running, in a new terminal list the queues.

    ::
        
        list-queues.sh

    Listing Queues broker=localhost:15672

    +-----------------------------------------------+-----------+----------+----------------+-------------------------+
    |                     name                      | consumers | messages | messages_ready | messages_unacknowledged |
    +-----------------------------------------------+-----------+----------+----------------+-------------------------+
    | celery.rabbit.sub                             | 1         | 0        | 0              | 0                       |
    +-----------------------------------------------+-----------+----------+----------------+-------------------------+
    | celery@localhost.localdomain.celery.pidbox    | 1         | 0        | 0              | 0                       |
    +-----------------------------------------------+-----------+----------+----------------+-------------------------+
    | celeryev.788d17cb-de2d-444e-9a02-2b75fe76298c | 1         | 0        | 0              | 0                       |
    +-----------------------------------------------+-----------+----------+----------------+-------------------------+
    | reporting.accounts                            | 1         | 0        | 0              | 0                       |
    +-----------------------------------------------+-----------+----------+----------------+-------------------------+

#.  Stop the Celery RabbitMQ Subscriber worker with ``ctrl + c``

    ::

        2017-12-09 11:02:39,678: INFO celery@localhost.localdomain ready.
        ^C
        worker: Hitting Ctrl+C again will terminate all running tasks!

        worker: Warm shutdown (MainProcess)

#.  List the Queues after shutting down the Celery RabbitMQ Subscriber

    Notice the ``reporting.accounts`` queue is still present even after stopping the worker.

    ::

        list-queues.sh 

    Listing Queues broker=localhost:15672

    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery.rabbit.sub  | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

#.  Inspect the Bindings for examining how RabbitMQ routes messages from Exchanges to Queues

    ::

        list-bindings.sh 

    Listing Bindings broker=localhost:15672

    +-------------------+--------------------+--------------------+
    |      source       |    destination     |    routing_key     |
    +-------------------+--------------------+--------------------+
    |                   | celery.rabbit.sub  | celery.rabbit.sub  |
    +-------------------+--------------------+--------------------+
    |                   | reporting.accounts | reporting.accounts |
    +-------------------+--------------------+--------------------+
    | celery.rabbit.sub | celery.rabbit.sub  | celery.rabbit.sub  |
    +-------------------+--------------------+--------------------+
    | reporting         | reporting.accounts | reporting.accounts |
    +-------------------+--------------------+--------------------+

Redis Kombu Subscriber
======================

If you do not want to use Celery, you can use the ``KombuSubscriber`` class to process messages. This class will wait for a configurable amount of seconds to consume a single message from the subscribed queue and then stop processing.

#.  Check the Redis keys

    ::

        redis-cli
        127.0.0.1:6379> keys *
        1) "_kombu.binding.reporting.accounts"
        2) "_kombu.binding.celery.redis.sub"
        127.0.0.1:6379> 

#.  Run the Redis Publisher

    ::

        run_redis_publisher.py 
        2017-12-09 11:46:39,743 - run-redis-publisher - INFO - Start - run-redis-publisher
        2017-12-09 11:46:39,743 - run-redis-publisher - INFO - Sending msg={'account_id': 123, 'created': '2017-12-09T11:46:39.743636'} ex=reporting.accounts rk=reporting.accounts
        2017-12-09 11:46:39,767 - redis-publisher - INFO - SEND - exch=reporting.accounts rk=reporting.accounts
        2017-12-09 11:46:39,770 - run-redis-publisher - INFO - End - run-redis-publisher sent=True

#.  Run the Redis Kombu Subscriber

    By default, this will wait for a single message to be delivered within 10 seconds.

    ::

        kombu_redis_subscriber.py 
        2017-12-09 11:47:58,798 - kombu-redis-subscriber - INFO - Start - kombu-redis-subscriber
        2017-12-09 11:47:58,798 - kombu-redis-subscriber - INFO - setup routing
        2017-12-09 11:47:58,822 - kombu-redis-subscriber - INFO - kombu-redis-subscriber - kombu.subscriber queues=reporting.accounts consuming with callback=handle_message
        2017-12-09 11:47:58,823 - kombu-redis-subscriber - INFO - callback received msg body={u'account_id': 123, u'created': u'2017-12-09T11:46:39.743636'}
        2017-12-09 11:47:58,824 - kombu-redis-subscriber - INFO - End - kombu-redis-subscriber

#.  Check the Redis keys

    Nothing should have changed:

    ::

        127.0.0.1:6379> keys *
        1) "_kombu.binding.reporting.accounts"
        2) "_kombu.binding.celery.redis.sub"
        127.0.0.1:6379> 

RabbitMQ Kombu Subscriber
=========================

If you do not want to use Celery, you can use the ``KombuSubscriber`` class to process messages. This class will wait for a configurable amount of seconds to consume a single message from the subscribed queue and then stop processing.

#.  List the Queues

    If the docker containers are still running the previous RabbitMQ pub/sub test will still have the queues, exchanges and bindings still left over. If not then skip this step.

    ::

        list-queues.sh 

    Listing Queues broker=localhost:15672

    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery.rabbit.sub  | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

#.  Run the RabbitMQ Subscriber

    Please note this output assumes there are no messages in the queue already from a previous test. It will wait for 10 seconds before stopping.

    ::

        kombu_rabbitmq_subscriber.py 
        2017-12-09 11:53:56,948 - kombu-rabbitmq-subscriber - INFO - Start - kombu-rabbitmq-subscriber
        2017-12-09 11:53:56,948 - kombu-rabbitmq-subscriber - INFO - setup routing
        2017-12-09 11:53:56,973 - kombu-rabbitmq-subscriber - INFO - kombu-rabbitmq-subscriber - kombu.subscriber queues=reporting.accounts consuming with callback=handle_message
        2017-12-09 11:54:06,975 - kombu-rabbitmq-subscriber - INFO - End - kombu-rabbitmq-subscriber

#.  Run the RabbitMQ Publisher

    ::

        run_rabbitmq_publisher.py 
        2017-12-09 11:56:42,793 - run-rabbitmq-publisher - INFO - Start - run-rabbitmq-publisher
        2017-12-09 11:56:42,793 - run-rabbitmq-publisher - INFO - Sending msg={'account_id': 456, 'created': '2017-12-09T11:56:42.793819'} ex=reporting rk=reporting.accounts
        2017-12-09 11:56:42,812 - rabbitmq-publisher - INFO - SEND - exch=reporting rk=reporting.accounts
        2017-12-09 11:56:42,814 - run-rabbitmq-publisher - INFO - End - run-rabbitmq-publisher sent=True

#.  Run the RabbitMQ Kombu Subscriber

    By default, this will wait for a single message to be delivered within 10 seconds.

    ::

        kombu_rabbitmq_subscriber.py 
        2017-12-09 11:57:07,047 - kombu-rabbitmq-subscriber - INFO - Start - kombu-rabbitmq-subscriber
        2017-12-09 11:57:07,047 - kombu-rabbitmq-subscriber - INFO - setup routing
        2017-12-09 11:57:07,103 - kombu-rabbitmq-subscriber - INFO - kombu-rabbitmq-subscriber - kombu.subscriber queues=reporting.accounts consuming with callback=handle_message
        2017-12-09 11:57:07,104 - kombu-rabbitmq-subscriber - INFO - callback received msg body={u'account_id': 456, u'created': u'2017-12-09T11:56:42.793819'}
        2017-12-09 11:57:07,104 - kombu-rabbitmq-subscriber - INFO - End - kombu-rabbitmq-subscriber

Running a Redis Message Processor
=================================

This will simulate setting up a processor that handles user conversion events using a Redis server.

#.  Start the User Conversion Event Processor

    ::

        start-kombu-message-processor-redis.py 
        2017-12-09 12:09:14,329 - loader-name - INFO - Start - msg-proc
        2017-12-09 12:09:14,329 - msg-proc - INFO - msg-proc START - consume_queue=user.events.conversions rk=None
        2017-12-09 12:09:14,329 - msg-sub - INFO - setup routing
        2017-12-09 12:09:14,351 - msg-sub - INFO - msg-sub - kombu.subscriber queues=user.events.conversions consuming with callback=process_message

#.  Publish a User Conversion Event
    
    From another terminal, publish a user conversion event

    ::

        publish-user-conversion-events-redis.py 
        2017-12-09 12:09:16,557 - publish-user-conversion-events - INFO - Start - publish-user-conversion-events
        2017-12-09 12:09:16,558 - publish-user-conversion-events - INFO - Sending user conversion event msg={'subscription_id': 456, 'created': '2017-12-09T12:09:16.558462', 'stripe_id': 789, 'account_id': 123, 'product_id': 'ABC'} ex=user.events rk=user.events.conversions
        2017-12-09 12:09:16,582 - publish-uce-redis - INFO - SEND - exch=user.events rk=user.events.conversions
        2017-12-09 12:09:16,585 - publish-user-conversion-events - INFO - End - publish-user-conversion-events sent=True

#.  Confirm the Processor handled the conversion event

    ::

        2017-12-09 12:09:16,587 - msg-proc - INFO - msg-proc proc start - msg body={u'subscription_id': 456, u'product_id': u'ABC', u'stripe_id': 789, u'account_id': 123, u'created': u'2017-12-09T12:09:16.558462'}
        2017-12-09 12:09:16,587 - msg-proc - INFO - No auto-caching or pub-hook set exchange=None
        2017-12-09 12:09:16,588 - msg-proc - INFO - msg-proc proc done - msg

#.  Check the Redis keys for the new User Conversion Events key

    ::

        redis-cli 
        127.0.0.1:6379> keys *
        1) "_kombu.binding.reporting.accounts"
        2) "_kombu.binding.user.events"
        3) "_kombu.binding.celery.redis.sub"
        4) "_kombu.binding.user.events.conversions"
        127.0.0.1:6379> 

Run a Message Processor from RabbitMQ with Relay Publish Hook to Redis
======================================================================

This could also be set up for auto-caching instead of this pub-sub flow because this delivers a post-processing json dictionary into a Redis key (publish hook), and let's be honest Redis is great at caching all the datas.

#.  Clear out the ``reporting.accounts`` Redis key

    Either run ``kombu_redis_subscriber.py`` until there's no more messages being consumed or you can restart the docker containers with the ``stop-redis-and-rabbitmq.sh`` and ``start-redis-and-rabbitmq.sh``, but the point is verify there's nothing in the ``reporting.accounts`` key (could just delete it with the ``redis-cli``).

#.  Start the Kombu RabbitMQ Message Processor

    ::

        start-kombu-message-processor-rabbitmq.py
        2017-12-09 12:25:09,962 - loader-name - INFO - Start - msg-proc
        2017-12-09 12:25:09,962 - msg-proc - INFO - msg-proc START - consume_queue=user.events.conversions rk=reporting.accounts
        2017-12-09 12:25:09,962 - msg-sub - INFO - setup routing
        2017-12-09 12:25:09,987 - msg-sub - INFO - msg-sub - kombu.subscriber queues=user.events.conversions consuming with callback=process_message

#.  Send a User Conversion Event to RabbitMQ

    ::

        publish-user-conversion-events-rabbitmq.py
        2017-12-09 12:25:35,167 - publish-user-conversion-events - INFO - Start - publish-user-conversion-events
        2017-12-09 12:25:35,167 - publish-user-conversion-events - INFO - Sending user conversion event msg={'subscription_id': 888, 'created': '2017-12-09T12:25:35.167891', 'stripe_id': 999, 'account_id': 777, 'product_id': 'XYZ'} ex=user.events rk=user.events.conversions
        2017-12-09 12:25:35,185 - publish-uce-rabbitmq - INFO - SEND - exch=user.events rk=user.events.conversions
        2017-12-09 12:25:35,187 - publish-user-conversion-events - INFO - End - publish-user-conversion-events sent=True

#.  Verify the Kombu RabbitMQ Message Processor Handled the Message

    Notice the ``pub-hook`` shows the relay-specific log lines

    ::

        2017-12-09 12:25:35,188 - msg-proc - INFO - msg-proc proc start - msg body={u'subscription_id': 888, u'product_id': u'XYZ', u'stripe_id': 999, u'account_id': 777, u'created': u'2017-12-09T12:25:35.167891'}
        2017-12-09 12:25:35,188 - msg-proc - INFO - msg-proc pub-hook - build - hook msg body
        2017-12-09 12:25:35,188 - msg-proc - INFO - msg-proc pub-hook - send - exchange=reporting.accounts rk=reporting.accounts sz=json
        2017-12-09 12:25:35,210 - msg-pub - INFO - SEND - exch=reporting.accounts rk=reporting.accounts
        2017-12-09 12:25:35,212 - msg-proc - INFO - msg-proc pub-hook - send - done exchange=reporting.accounts rk=reporting.accounts res=True
        2017-12-09 12:25:35,212 - msg-proc - INFO - msg-proc proc done - msg

#.  Process the Redis ``reporting.accounts`` queue

    This could also be cached data about the user that made this purchase like a write-through-cache.

    ::

        kombu_redis_subscriber.py 
        2017-12-09 12:26:21,846 - kombu-redis-subscriber - INFO - Start - kombu-redis-subscriber
        2017-12-09 12:26:21,846 - kombu-redis-subscriber - INFO - setup routing
        2017-12-09 12:26:21,867 - kombu-redis-subscriber - INFO - kombu-redis-subscriber - kombu.subscriber queues=reporting.accounts consuming with callback=handle_message
        2017-12-09 12:26:21,869 - kombu-redis-subscriber - INFO - callback received msg body={u'data': {}, u'org_msg': {u'subscription_id': 888, u'created': u'2017-12-09T12:25:35.167891', u'stripe_id': 999, u'product_id': u'XYZ', u'account_id': 777}, u'hook_created': u'2017-12-09T12:25:35.188420', u'version': 1, u'source': u'msg-proc'}
        2017-12-09 12:26:21,870 - kombu-redis-subscriber - INFO - End - kombu-redis-subscriber

SQS - Experimental
==================

I have opened a PR for fixing the kombu http client.

#.  Export your AWS Key and Secret Key

    ::

        export SQS_AWS_ACCESS_KEY=<ACCESS KEY>
        export SQS_AWS_SECRET_KEY=<SECRET KEY>

#.  Publish to SQS

    ::

        kombu_sqs_publisher.py 
        2017-12-09 12:49:24,900 - kombu-sqs-publisher - INFO - Start - kombu-sqs-publisher
        2017-12-09 12:49:24,901 - kombu-sqs-publisher - INFO - Sending user conversion event msg={'subscription_id': 222, 'product_id': 'DEF', 'stripe_id': 333, 'account_id': 111, 'created': '2017-12-09T12:49:24.901513'} ex=test1 rk=test1
        2017-12-09 12:49:25,007 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
        2017-12-09 12:49:25,538 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
        2017-12-09 12:49:26,237 - kombu-sqs-publisher - INFO - SEND - exch=test1 rk=test1
        2017-12-09 12:49:26,352 - kombu-sqs-publisher - INFO - End - kombu-sqs-publisher sent=True

#.  Subscribe to SQS

    Please see the debugging section for getting this to function with kombu 4.1.0 

    https://github.com/jay-johnson/celery-connectors#temporary-fix-for-kombu-sqs
    
    ::
    
        kombu_sqs_subscriber.py 
        2017-12-09 12:49:41,232 - kombu-sqs-subscriber - INFO - Start - kombu-sqs-subscriber
        2017-12-09 12:49:41,232 - kombu-sqs-subscriber - INFO - setup routing
        2017-12-09 12:49:41,333 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
        2017-12-09 12:49:41,801 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
        2017-12-09 12:49:42,517 - kombu-sqs-subscriber - INFO - kombu-sqs-subscriber - kombu.subscriber queues=test1 consuming with callback=handle_message
        2017-12-09 12:49:42,671 - kombu-sqs-subscriber - INFO - callback received msg body={u'subscription_id': 222, u'created': u'2017-12-09T12:49:24.901513', u'stripe_id': 333, u'product_id': u'DEF', u'account_id': 111}
        2017-12-09 12:49:42,773 - kombu-sqs-subscriber - INFO - End - kombu-sqs-subscriber

#.  Verify the SQS Queue ``test1`` is empty

    ::
    
        aws sqs receive-message --queue-url https://queue.amazonaws.com/<YOUR QUEUE ID>/test1
        echo $?
        0

Simple Pub Sub with an Existing Celery Task
===========================================

Start the Celery Worker as an Ecommerce Subscriber
--------------------------------------------------

Please run this from the base directory of the repository in a terminal that has sourced the virtual env: ``source venv/bin/activate``.

::

    ./start-ecomm-worker.sh 
    
    -------------- celery@ecommerce_subscriber v4.1.0 (latentcall)
    ---- **** ----- 
    --- * ***  * -- Linux-4.7.4-200.fc24.x86_64-x86_64-with-fedora-24-Twenty_Four 2017-12-10 15:12:11
    -- * - **** --- 
    - ** ---------- [config]
    - ** ---------- .> app:         ecommerce-worker:0x7fae3cfa2198
    - ** ---------- .> transport:   amqp://rabbitmq:**@localhost:5672//
    - ** ---------- .> results:     rpc://
    - *** --- * --- .> concurrency: 4 (prefork)
    -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
    --- ***** ----- 
    -------------- [queues]
                    .> celery           exchange=celery(direct) key=celery
                    

    [tasks]
    . ecomm_app.ecommerce.tasks.handle_user_conversion_events

    [2017-12-10 15:12:11,727: INFO/MainProcess] Connected to amqp://rabbitmq:**@127.0.0.1:5672//
    [2017-12-10 15:12:11,740: INFO/MainProcess] mingle: searching for neighbors
    [2017-12-10 15:12:12,776: INFO/MainProcess] mingle: all alone
    [2017-12-10 15:12:12,828: INFO/MainProcess] celery@ecommerce_subscriber ready.
    [2017-12-10 15:12:13,633: INFO/MainProcess] Events of group {task} enabled by remote.


Publish User Conversion Events to the Celery Ecommerce Subscriber
-----------------------------------------------------------------

Please run this from a separate terminal that has sourced the virtual env: ``source venv/bin/activate``.

#.  Change to the ``ecomm_app`` directory

    ::
    
        cd ecomm_app

#.  Publish a task

    This will use the Celery ``send_task`` method to publish the Celery task: ``ecomm_app.ecommerce.tasks.handle_user_conversion_events`` to RabbitMQ which is monitored by the Celery ecommerce worker.

    ::

        ./publish_task.py 
        INFO:celery-task-publisher:Sending broker=amqp://rabbitmq:rabbitmq@localhost:5672// body={'subscription_id': 321, 'msg_id': '6d7ab602-f7cd-4d90-a0c5-5eb0cdcb41d9', 'version': 1, 'product_id': 'JJJ', 'account_id': 999, 'stripe_id': 876, 'created': '2017-12-10T15:16:08.557804'}
        INFO:celery-task-publisher:Done with msg_id=6d7ab602-f7cd-4d90-a0c5-5eb0cdcb41d9 result=True

Confirm the Celery Worker Processed the Conversion Message
----------------------------------------------------------

::

    [2017-12-10 15:16:08,593: INFO/MainProcess] Received task: ecomm_app.ecommerce.tasks.handle_user_conversion_events[9349e1be-fca5-40b5-86d3-0661fdd9fd06]  
    [2017-12-10 15:16:08,594: INFO/ForkPoolWorker-4] task - user_conversion_events - start body={'stripe_id': 876, 'version': 1, 'subscription_id': 321, 'created': '2017-12-10T15:16:08.557804', 'account_id': 999, 'product_id': 'JJJ', 'msg_id': '6d7ab602-f7cd-4d90-a0c5-5eb0cdcb41d9'}
    [2017-12-10 15:16:08,595: INFO/ForkPoolWorker-4] task - user_conversion_events - done
    [2017-12-10 15:16:08,619: INFO/ForkPoolWorker-4] Task ecomm_app.ecommerce.tasks.handle_user_conversion_events[9349e1be-fca5-40b5-86d3-0661fdd9fd06] succeeded in 0.025004414000250108s: True

Check the Ecommerce Subscriber in Flower
----------------------------------------

The Ecommerce Publisher and Subscriber are using RabbitMQ which is registered under the Flower url:

http://localhost:5555/ - (login: admin/admin)

There should be a Worker named:

::

    celery@ecommerce_subscriber

There are also additional worker details available at:

http://localhost:5555/worker/celery@ecommerce_subscriber

View the registered ecommerce tasks for the worker:

http://localhost:5555/worker/celery@ecommerce_subscriber#tab-tasks

Debugging with rabbitmqadmin
=============================

The pip and development build will install ``rabbitmqadmin`` (https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.0/bin/rabbitmqadmin) version 3.7.0. It is a great utility for verifying RabbitMQ messaging and does not require having access to the RabbitMQ cluster's host nodes (or a machine with rabbitmqctl on it).

Please note: ``rabbitmqadmin`` uses the management HTTP port (not the amqp port 5672) which requires a broker to have the management plugin enabled to work if you're using this with an external RabbitMQ cluster.

Checking queues
---------------

Script in pip

::

    list-queues.sh 

    Listing Queues broker=localhost:15672

    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery             | 0         | 0        | 0              | 0                       |
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

Manual way

::

    rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list queues
    +--------------------+-----------+----------+----------------+-------------------------+
    |        name        | consumers | messages | messages_ready | messages_unacknowledged |
    +--------------------+-----------+----------+----------------+-------------------------+
    | celery             | 0         | 0        | 0              | 0                       |
    | reporting.accounts | 0         | 0        | 0              | 0                       |
    +--------------------+-----------+----------+----------------+-------------------------+

Checking exchanges
------------------

Script in pip

::

    list-exchanges.sh 

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

    rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list exchanges name typa
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

List Bindings
=============

Script in pip

::

    list-bindings.sh 

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

    rabbitmqadmin.py --host=localhost --port=15672 --username=rabbitmq --password=rabbitmq list bindings source destination routing_key
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

    The tests require the docker containers to be running prior to starting.

    ::

        python setup.py test

Debugging
=========

pycURL Reinstall with NSS
-------------------------

For anyone wanting to use kombu SQS, I had to uninstall ``pycurl`` and install it with ``nss``.

The error looked like this in the logs:

::

    2017-12-09 12:28:46,811 - kombu-sqs-subscriber - INFO - kombu-sqs-subscriber - kombu.subscriber consume hit exception=The curl client requires the pycurl library. queue=test1


So I opened up a python shell

Python 2:

::

    $ python
    Python 2.7.12 (default, Sep 29 2016, 13:30:34) 
    [GCC 6.2.1 20160916 (Red Hat 6.2.1-2)] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import pycurl
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "build/bdist.linux-x86_64/egg/pycurl.py", line 7, in <module>
    File "build/bdist.linux-x86_64/egg/pycurl.py", line 6, in __bootstrap__
    ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (none/other)
    >>> 

Python 3:

::

    $ python
    Python 3.5.3 (default, May 11 2017, 09:10:41) 
    [GCC 6.3.1 20161221 (Red Hat 6.3.1-1)] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import pycurl
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
    ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (none/other)
    >>> 

Uninstalled and Reinstalled pycurl with nss

::

    pip uninstall -y pycurl; pip install pycurl --compile --global-option="--with-nss" pycurl

Temporary fix for Kombu SQS
---------------------------

SQS Kombu Subscriber ``'NoneType' object has no attribute 'call_repeatedly'``

Until Kombu fixes the SQS transport and publishes it to pypi, the SQS subscriber will throw exceptions like below.

::

    kombu_sqs_subscriber.py 
    2017-12-09 12:30:45,493 - kombu-sqs-subscriber - INFO - Start - kombu-sqs-subscriber
    2017-12-09 12:30:45,493 - kombu-sqs-subscriber - INFO - setup routing
    2017-12-09 12:30:45,602 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
    2017-12-09 12:30:46,046 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
    2017-12-09 12:30:46,832 - kombu-sqs-subscriber - INFO - kombu-sqs-subscriber - kombu.subscriber queues=test1 consuming with callback=handle_message
    2017-12-09 12:30:46,989 - kombu-sqs-subscriber - INFO - callback received msg body={u'subscription_id': 222, u'created': u'2017-12-09T12:28:28.093582', u'stripe_id': 333, u'product_id': u'DEF', u'account_id': 111}
    2017-12-09 12:30:46,994 - kombu-sqs-subscriber - INFO - kombu-sqs-subscriber - kombu.subscriber consume hit exception='NoneType' object has no attribute 'call_repeatedly' queue=test1
    2017-12-09 12:30:46,994 - kombu-sqs-subscriber - INFO - End - kombu-sqs-subscriber
    Restoring 1 unacknowledged message(s)

Notice the last line has put the message into SQS in-flight which means it has not been acknowledged or deleted.

You can verify this message is still there with the aws cli:

::

    aws sqs receive-message --queue-url https://queue.amazonaws.com/<YOUR QUEUE ID>/test1
    {
        "Messages": [
            {
                "Body": "eyJib2R5IjogImV5SnpkV0p6WTNKcGNIUnBiMjVmYVdRaU9pQXlNaklzSUNKd2NtOWtkV04wWDJsa0lqb2dJa1JGUmlJc0lDSnpkSEpwY0dWZmFXUWlPaUF6TXpNc0lDSmhZMk52ZFc1MFgybGtJam9nTVRFeExDQWlZM0psWVhSbFpDSTZJQ0l5TURFM0xURXlMVEE1VkRFeU9qVXpPakEwTGpjME9UY3lOaUo5IiwgImhlYWRlcnMiOiB7fSwgImNvbnRlbnQtdHlwZSI6ICJhcHBsaWNhdGlvbi9qc29uIiwgInByb3BlcnRpZXMiOiB7InByaW9yaXR5IjogMCwgImJvZHlfZW5jb2RpbmciOiAiYmFzZTY0IiwgImRlbGl2ZXJ5X2luZm8iOiB7InJvdXRpbmdfa2V5IjogInRlc3QxIiwgImV4Y2hhbmdlIjogInRlc3QxIn0sICJkZWxpdmVyeV9tb2RlIjogMiwgImRlbGl2ZXJ5X3RhZyI6ICJkOGI3MjNiMi05MDVkLTQxZTEtODVlNy00NjUwZGY2NWU2MTgifSwgImNvbnRlbnQtZW5jb2RpbmciOiAidXRmLTgifQ==", 
                "ReceiptHandle": "AQEBDnxqT1+SOam1ZtMKPgh77a8bapLbcrI3PZRTqVZJokz0h7oMusuJPAB9jksH3BQHQyg3TyZXasBblpMcin3HTzh7ykTgAgawhMreOoWGGiaeEoOekaChn2yFpKDbVP1ZENRVcpAzeDXzCd52TITZbyLk8FY1PJB3XpAiih9SH/R0FPj3JnU0WTxjTAWtBnSlUUGXFc3CczJi61YsJS+bTZs8JIgDaICMF+zMhnV+rV4zXDObTVFM3OaMdf/puqZ9yRd3fM1GsOxZaDNRDGYKml/UK0tn32gtqPSuUW905YamwnWQYB9mF338Jgx11rv78b5lLogpU/0t6E+0tD1Lkr/UR/M64NZI2eTwp6ZHNtqTNbkjd5VsBgB39b+wXFFn", 
                "MD5OfBody": "e72609877b90ad86df2f161c6303eaf0", 
                "MessageId": "684328b4-a38c-4868-8550-e0d46599a0c2"
            }
        ]
    }

If you're feeling bold, you can run off my PR fix branch as well:

::
    
    pip uninstall -y kombu ; rm -rf /tmp/sqs-pr-fix-with-kombu; git clone https://github.com/jay-johnson/kombu.git /tmp/sqs-pr-fix-with-kombu && pushd /tmp/sqs-pr-fix-with-kombu && git checkout sqs-http-get-client && python setup.py develop && popd

With the SQS fix applied locally (works on python 2 and 3 on my fedora 24 vm):

::

    2017-12-09 12:47:12,177 - kombu-sqs-subscriber - INFO - Start - kombu-sqs-subscriber
    2017-12-09 12:47:12,177 - kombu-sqs-subscriber - INFO - setup routing
    2017-12-09 12:47:12,295 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
    2017-12-09 12:47:12,736 - botocore.vendored.requests.packages.urllib3.connectionpool - INFO - Starting new HTTPS connection (1): queue.amazonaws.com
    2017-12-09 12:47:13,454 - kombu-sqs-subscriber - INFO - kombu-sqs-subscriber - kombu.subscriber queues=test1 consuming with callback=handle_message
    2017-12-09 12:47:13,592 - kombu-sqs-subscriber - INFO - callback received msg body={u'subscription_id': 222, u'created': u'2017-12-09T12:28:28.093582', u'stripe_id': 333, u'product_id': u'DEF', u'account_id': 111}
    2017-12-09 12:47:13,689 - kombu-sqs-subscriber - INFO - End - kombu-sqs-subscriber

After running it you can confirm the message has been deleted and acknowledged with the aws cli:

::

    aws sqs receive-message --queue-url https://queue.amazonaws.com/<YOUR QUEUE ID>/test1
    echo $?
    0

Testing
=======

Start the Relay
---------------

::

    ./start-ecomm-relay.py

Start the Celery Worker
-----------------------

::

    ./start-ecomm-worker.sh

Load Test Celery Worker over RabbitMQ
-------------------------------------

This will send 50,000 messages over with the Celery ``send_task`` method. As long as the ecomm Celery worker is running the messages will be sent over.

::

    python -m unittest tests/load_test_worker_rabbitmq.py

Load Test Relay
---------------

This will send 50,000 messages over the ``user.events.conversions`` RabbitMQ queue for the ecomm relay to process and then send to the ecomm worker.

::

    python -m unittest tests/load_test_relay_rabbitmq.py
    
Linting
-------

::

    pycodestyle --max-line-length=160 --exclude=venv,build,.tox,celery_connectors/rabbitmq/rabbitmqadmin.py

License
-------

Apache 2.0 - Please refer to the LICENSE_ for more details

.. _License: https://github.com/jay-johnson/celery-connectors/blob/master/LICENSE
