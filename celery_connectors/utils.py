import os


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
