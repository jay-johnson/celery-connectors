import os
import uuid
import random
import datetime


SUCCESS = 0
FAILED = 1
ERROR = 2
READY = 0
NOT_READY = 1


def ev(k, v):
    return os.getenv(k, v).strip().lstrip()
# end of ev


def get_percent_done(progress, total):
    if int(total) == 0:
        return 0
    else:
        return "%0.2f" % float(float(progress)/float(total)*100.00)
# end of get_percent_done


def calc_backoff_timer(num=0, sleep_secs=2.0):
    sleep_duration_in_seconds = sleep_secs
    if num > 0:
        sleep_duration_in_seconds = float((num * 1.5) * sleep_secs)
        if sleep_duration_in_seconds > 60.0:
            sleep_duration_in_seconds = 60.0
    return sleep_duration_in_seconds
# end of calc_backoff_timer


def build_msg_id(max_len=10):
    return str(uuid.uuid4()).replace("-", "")[0:max_len]
# end of build_msg_id


def build_msg(data={}, version=1, max_id_len=10):
    now = datetime.datetime.now().isoformat()
    msg_id = "{}_{}".format(build_msg_id(max_id_len), version)

    msg = {"msg_id": msg_id,
           "created": now,
           "data": data}
    return msg
# end of build_msg


def build_sample_msgs(num=100,
                      data={},
                      version=1):

    msgs = []
    if num < 1:
        return msgs

    num_done = 0
    while num_done < num:
        new_msg = build_msg(data=data,
                            version=version)
        msgs.append(new_msg)
        num_done += 1
    # end of building them

    return msgs
# end of build_sample_msgs


def get_exchange_from_msg(msg):
    try:
        return msg.delivery_info["exchange"]
    except Exception:
        return ""
# end of get_exchange_from_msg


def get_routing_key_from_msg(msg):
    try:
        return msg.delivery_info["routing_key"]
    except Exception:
        return ""
# end of get_routing_key_from_msg


def get_source_info_from_msg(msg):
    src_exchange = get_exchange_from_msg(msg)
    src_routing_key = get_routing_key_from_msg(msg)
    source_info = {"src_exchange": src_exchange,
                   "src_routing_key": src_routing_key}
    return source_info
# end of get_source_info_from_msg


def get_random_float(use_min=1.0, use_max=10.0):
    return random.uniform(use_min, use_max)
# end of get_random_float
