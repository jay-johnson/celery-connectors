import os
import uuid
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


def build_msg(data={}, version=1):
    now = datetime.datetime.now().isoformat()
    msg = {"msg_id": "{}_{}".format(str(uuid.uuid4()), version),
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
