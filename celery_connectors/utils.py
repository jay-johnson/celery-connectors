import os


def ev(k, v):
    test = os.getenv(k, v).strip().lstrip()
    return test
# end of ev
