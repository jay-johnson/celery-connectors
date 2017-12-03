import os
import sys
import datetime

try:
    # Python 2 should use cPickle for speed
    import cPickle as pickle
except ImportError:
    # Python 3 has native cPickle with just the import pickle
    import pickle

from redis import Redis
from time import sleep


class RedisWrapper(object):

    def __init__(self, name, serializer=pickle, **kwargs):

        self.m_debug = False
        self.m_name = name
        self.m_theserializer = serializer
        self.m_redis = Redis(**kwargs)
        self.m_retry_interval = 1
        self.m_retry_count = 1
        self.m_max_retries = -1
        self.m_max_sleep_secs = 30  # 30 seconds

        self.m_host = ""
        self.m_port = ""
        self.m_address = ""
        self.m_id = "Name(" + str(self.m_name) + ")"

        for key, value in kwargs.items():
            if str(key) == "host":
                self.m_host = str(value)
            if str(key) == "port":
                self.m_port = str(value)

        if self.m_host != "" and self.m_port != "":
            self.m_id = "Name(" + str(self.m_name) + ") RedisAddress(" + str(self.m_host) + ":" + str(self.m_port) + ")"
            self.m_address = str(self.m_host) + ":" + str(self.m_port)

        self.m_error_log = "/tmp/__redis_errors.log"
        self.m_state = "Disconnected"
    # end of __init__

    def log_retry(self, fn_name, ex):
        cmd_line = "/usr/bin/echo '{} - redis app " + \
                   "- {} ex={}' > {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                             fn_name,
                                             ex,
                                             self.m_error_log)
        os.system("{}".format(cmd_line))
    # end of log_retry

    def retry_throttled_connection(self, ex, debug=False):

        msg = "ERROR - {} - {} - RW EX - {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                                                    self.m_id,
                                                    ex)

        # append to the error log
        with open(self.m_error_log, "a") as output_file:
            output_file.write(str(msg))

        try:
            self.m_state = "Disconnected"
            cur_sleep = (self.m_retry_interval * self.m_retry_count) + 1
            if debug:
                print("Retrying Connection")
            while self.m_state == "Disconnected":

                try:
                    msg = self.safe_get_cached_single_set("RetryingRedisConnection")

                    if "Status" in msg and str(msg["Status"]) != "EXCEPTION":
                        if debug:
                            print("------")
                            print("SUCCESS(" + str(msg) + ")")
                            print(str(msg))
                            print("")
                        self.m_state = "Connected"

                except Exception as e:
                    if debug:
                        print("Redis Failed Connection Retry(" + str(e) + ")")

                if self.m_state != "Connected":
                    cur_sleep = (self.m_retry_interval * self.m_retry_count) + 1
                    if cur_sleep > self.m_max_sleep_secs:
                        cur_sleep = self.m_max_sleep_secs
                        if debug:
                            print("---MAX SLEEP(" + str(self.m_max_sleep_secs) + ") HIT")
                    else:
                        self.m_retry_count += 1
                        self.m_retry_interval += 2

                    if debug:
                        print(" - Sleeping before Retry(" + str(cur_sleep) + ")")
                    sleep(cur_sleep)

            # end of while disconnected
            if debug:
                print("Retrying Connection - SUCCESS")

            self.m_retry_count = 1
            self.m_retry_interval = 1

        except Exception as k:
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")
            print("ERROR: Redis Retry Connection had Critical Failure(" + str(k) + ")")

        # end of try/ex

        msg = "Retry Completed - {} - {} - RW.m_state={}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                                                                 self.m_id,
                                                                 self.m_state)

        # append to the error log
        with open(self.m_error_log, "a") as output_file:
            output_file.write(str(msg))

        if debug:
            print(msg)

        return True
    # end of retry_throttled_connection

    def client_kill(self):

        try:
            self.m_redis.connection_pool.get_connection("QUIT").disconnect()
            self.m_state = "Disconnected"
        except Exception as p:
            print("ERROR: Failed to Kill: " + str(self.m_id) + " with Ex(" + str(p) + ")")
            self.m_state = "Disconnected"

        return None
    # end of client_kill

    def __rlen(self):
        success = False
        while not success:
            try:
                return self.m_redis.llen(self.key())

                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
        # end of while not success
    # end of __rlen

    def allconsume(self, **kwargs):
        success = False
        while not success:
            try:
                kwargs.setdefault('block', True)
                try:
                    while True:
                        msg = self.get(**kwargs)
                        if msg is None:
                            break
                        yield msg
                except KeyboardInterrupt:
                    print("")
                    return
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
        # end of while not success
    # end of allconsume

    def key(self):
        success = False
        while not success:
            try:
                return "%s" % self.m_name
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
        # end of while not success
    # end of key

    def get_cached_multiple_set(self, start_idx=0, end_idx=-1, queue=None):
        success = False
        while not success:
            try:

                msg = None

                if not queue:
                    msg = self.m_redis.lrange(self.key(), start_idx, end_idx)
                    return msg
                else:
                    msg = self.m_redis.lrange(queue, start_idx, end_idx)
                    return msg

                if msg is not None and self.m_theserializer is not None:

                    try:

                        # py2/py3
                        if sys.version_info < (2, 8):
                            msg = self.m_theserializer.loads(msg[0])
                        else:
                            try:
                                msg = self.m_theserializer.loads(msg[0])
                            except Exception:
                                msg = self.m_theserializer.loads(msg[0].decode("utf-8"))
                        # end of py2/py3 serialization handling

                        return msg

                    except Exception as w:
                        print("redis app - get_cached_multiple_set ex=" + str(w))
                        self.log_retry("get_cached_multiple_set", w)
                    # end of try/ex

                # end of if msg

                return msg
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of get_cached_multiple_set

    def safe_get_cached_single_set(self, key):
        success = False
        while not success:
            try:

                msg = {"Value": None, "Status": None, "Exception": None}
                try:
                    cached_msg = self.m_redis.lrange(key, 0, 1)
                    new_msg = None

                    if cached_msg is not None and len(cached_msg) != 0 and self.m_theserializer is not None:

                        try:

                            # py2/py3
                            if sys.version_info < (2, 8):
                                new_msg = self.m_theserializer.loads(cached_msg[0])
                            else:
                                try:
                                    new_msg = self.m_theserializer.loads(cached_msg[0])
                                except Exception:
                                    new_msg = self.m_theserializer.loads(cached_msg[0].decode("utf-8"))
                            # end of py2/py3 serialization handling

                        except Exception as w:
                            print("redis app - safe_get_cached_single_set ex=" + str(w))
                            self.log_retry("safe_get_cached_single_set 1", w)
                        # end of try/ex

                    # end of deserializing

                    msg["Value"] = new_msg
                    msg["Status"] = "SUCCESS"

                except Exception as e:
                    msg["Status"] = "EXCEPTION"
                    msg["Exception"] = "Exception(" + str(e) + ")"
                    print("redis app - safe_get_cached_single_set ex=" + str(e))
                    self.log_retry("safe_get_cached_single_set 2", e)
                # end of exception

                return msg
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of safe_get_cached_single_set

    def get_cached_single_set(self, queue=None):
        success = False
        while not success:
            try:

                msg = None

                if not queue:
                    msg = self.m_redis.lrange(self.key(), 0, 1)
                    return msg
                else:
                    msg = self.m_redis.lrange(queue, 0, 1)
                    return msg

                if msg is not None and self.m_theserializer is not None:

                    try:

                        # py2/py3
                        if sys.version_info < (2, 8):
                            msg = self.m_theserializer.loads(msg[0])
                        else:
                            try:
                                msg = self.m_theserializer.loads(msg[0])
                            except Exception:
                                msg = self.m_theserializer.loads(msg[0].decode("utf-8"))
                        # end of py2/py3 serialization handling

                        return msg

                    except Exception as w:
                        print("redis app - get_cached_single_set ex=" + str(w))
                        self.log_retry("get_cached_single_set", w)
                    # end of try/ex

                    return msg
                # end of if msg

                return msg
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of get_cached_single_set

    def get(self, block=False, timeout=None, queue=None):
        success = False
        while not success:
            try:

                msg = None
                if block:
                    if timeout is None:
                        timeout = 0

                    if not queue:
                        msg = self.m_redis.blpop(self.key(), timeout=timeout)
                    else:
                        msg = self.m_redis.blpop(queue, timeout=timeout)

                    if msg is not None:
                        msg = msg[1]
                else:
                    if not queue:
                        msg = self.m_redis.lpop(self.key())
                    else:
                        msg = self.m_redis.lpop(queue)

                if msg is not None and self.m_theserializer is not None:

                    try:

                        # py2/py3
                        if sys.version_info < (2, 8):
                            msg = self.m_theserializer.loads(msg)
                        else:
                            try:
                                msg = self.m_theserializer.loads(msg)
                            except Exception:
                                msg = self.m_theserializer.loads(msg.decode("utf-8"))
                        # end of py2/py3 serialization handling

                        return msg

                    except Exception as w:
                        print("redis app - get ex=" + str(w))
                        self.log_retry("get", w)
                    # end of try/ex

                # end of if msg

                return msg
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of get

    def put_into_key(self, key, *msgs):
        success = False
        while not success:
            try:
                if self.m_theserializer is not None:
                    msgs = map(self.m_theserializer.dumps, msgs)
                self.m_redis.rpush(key, *msgs)
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of put_into_key

    def put(self, *msgs):
        success = False
        while not success:
            try:
                if self.m_theserializer is not None:
                    msgs = map(self.m_theserializer.dumps, msgs)
                self.m_redis.rpush(self.key(), *msgs)
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of put

    def exists(self, key):
        success = False
        while not success:
            try:
                return self.m_redis.exists(key)
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of exists

    def delete_cache(self, queue=None):
        success = False
        while not success:
            try:
                if not queue:
                    self.m_redis.delete(self.key())
                else:
                    self.m_redis.delete(queue)
                return None
                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of delete_cache

    def flush_all(self):
        success = False
        while not success:
            try:

                self.m_redis.flushall()
                return None

                success = True
            except Exception as R:
                # try to reconnect with a throttle
                self.retry_throttled_connection(R)
            # end try/ex
        # end of while not successful
    # end of flush_all

# end of class RedisWrapper
