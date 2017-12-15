import logging
import time
from kombu import Connection
from celery_connectors.utils import SUCCESS
from celery_connectors.utils import calc_backoff_timer
from celery_connectors.utils import get_percent_done
import celery_connectors.mixin_send_task_msg


log = logging.getLogger("pub")


def run_publisher(broker_url,
                  exchange=None,     # kombu.Exchange object
                  routing_key=None,  # string
                  msgs=[],
                  num_per_batch=-1,
                  priority="high",
                  priority_routing={},
                  serializer="json",
                  ssl_options={},
                  transport_options={},
                  send_method=None,
                  silent=True,
                  publish_silent=False,
                  log_label="pub",
                  *args,
                  **kwargs):

    verbose = not silent

    if verbose:
        log.debug("connecting")

    with Connection(broker_url,
                    ssl=ssl_options,
                    transport_options=transport_options) as conn:

        num_to_send = len(msgs)

        if num_to_send == 0:
            log.info(("no msgs={} to publish")
                     .format(num_to_send))
            return

        use_send_method = send_method
        # use the default method for sending if one is not passed in
        if not use_send_method:
            use_send_method = celery_connectors.mixin_send_task_msg.mixin_send_task_msg

        if verbose:
            log.debug(("publishing ex={} rk={} "
                       "msgs={} send_method={}")
                      .format(exchange,
                              routing_key,
                              num_to_send,
                              use_send_method.__name__))

        num_sent = 0
        not_done = True
        num_fails = 0

        while not_done:

            cur_msg = msgs[num_sent]

            hide_logs = publish_silent
            if num_sent > 1 and num_sent % 200 == 0:
                hide_logs = False
                log.info(("{} send done "
                          "msg={}/{} ex={} rk={}")
                         .format(get_percent_done(
                                    num_sent,
                                    num_to_send),
                                 num_sent,
                                 num_to_send,
                                 exchange.name,
                                 routing_key))

            send_res = use_send_method(conn=conn,
                                       data=cur_msg,
                                       exchange=exchange,
                                       routing_key=routing_key,
                                       priority=priority,
                                       priority_routing=priority_routing,
                                       serializer=serializer,
                                       silent=hide_logs,
                                       log_label=log_label)

            if send_res["status"] == SUCCESS:
                num_fails = 0
                num_sent += 1
                if num_sent >= num_to_send:
                    not_done = False
            else:
                num_fails += 1
                sleep_duration = calc_backoff_timer(num_fails)
                log.info(("publish failed - {} - exch={} rk={} "
                          "sleep={} seconds retry={}")
                         .format(send_res["error"],
                                 exchange,
                                 routing_key,
                                 sleep_duration,
                                 num_fails))

                if num_fails > 100000:
                    num_fails = 1

                time.sleep(sleep_duration)
            # end of if done

        # end of sending all messages

    # end of with kombu.Connection

# end of run_publisher
