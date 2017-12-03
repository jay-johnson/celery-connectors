import os


def ev(k, v):
    return os.getenv(k, v).strip().lstrip()
# end of ev
