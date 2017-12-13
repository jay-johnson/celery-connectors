import logging
from kombu.common import maybe_declare
from kombu.pools import producers
from celery_connectors.utils import SUCCESS
from celery_connectors.utils import FAILED
from celery_connectors.utils import ERROR


name = "pub_send"
log = logging.getLogger(name)


def mixin_send_task_msg(conn=None,
                        data={},
                        exchange=None,     # kombu.Exchange object
                        routing_key=None,  # string
                        priority="high",
                        priority_routing={},
                        serializer="json",
                        **kwargs):

    res = {"status": ERROR,  # non-zero is failure
           "error": ""}

    use_routing_key = routing_key
    if not use_routing_key:
        if priority in priority_routing:
            use_routing_key = priority_routing[priority]
    # end of finding the routing key

    payload = data
    if len(payload) == 0:
        res["status"] = ERROR
        res["error"] = "Please set a data argument to a dict " + \
                       "to publish messages"
        return res

    if not conn:
        res["status"] = ERROR
        res["error"] = "Please set a valid connection (conn) " + \
                       "to publish messages"
        return res

    if not exchange:
        res["status"] = ERROR
        res["error"] = "Please set an exchange to publish"
        return res

    if not use_routing_key:
        res["status"] = ERROR
        res["error"] = "Please set pass in a routing_key " + \
                       "or a valid priority_routing with an" + \
                       "entry to a routing_key string to " + \
                       "send a task message"
        return res

    log.info(("{} publish - "
              "ex={} rk={} sz={}")
             .format(name,
                     exchange,
                     use_routing_key,
                     serializer))

    last_step = "try"
    try:
        with producers[conn].acquire(block=True) as producer:

            # if you throw here, please pass in a kombu.Exchange
            # because the type of Exchange should not be handled in
            # the send method
            last_step = "Please set an exchange to publish"
            last_step = "maybe declare={}".format(exchange.name)
            maybe_declare(exchange,
                          producer.channel)

            last_step = "publish rk={}".format(routing_key)
            producer.publish(payload,
                             serializer=serializer,
                             exchange=exchange,
                             routing_key=routing_key)

        res["status"] = SUCCESS
        res["error"] = ""

    except Exception as e:
        res["status"] = FAILED
        res["error"] = ("{} producer threw "
                        "exception={} ex={} rk={} "
                        "last_step={}").format(
                            name,
                            e,
                            exchange,
                            routing_key,
                            last_step)

        log.error(("{} producer threw "
                   "exception={} ex={} rk={} "
                   "last_step={}")
                  .format(name,
                          e,
                          exchange,
                          routing_key,
                          last_step))
    # end of try to send

    return res
# end of mixin_send_task_msg
