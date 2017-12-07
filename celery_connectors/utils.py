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
