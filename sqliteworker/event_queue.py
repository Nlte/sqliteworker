# mostly taken from Andrea Micheloni blog post
# https://m7i.org/tutorials/python-event-queue-concurrency-modeling/

import threading
import collections


class UnprocessedException(Exception):

    def __init__(self, reason):
        self._reason = reason

    def __str__(self):
        return str(self._reason)

    def __repr__(self):
        return 'UnprocessedException("%s")' % str(self)


class Queue(object):

    def __init__(self):
        self._queue = collections.deque([])
        self._condition = threading.Condition()

    def put(self, item, priority_flag=False):
        with self._condition:
            if priority_flag:
                self._queue.append(item)
            else:
                self._queue.appendleft(item)
            self._condition.notify()

    def qsize(self):
        with self._condition:
            return len(self._queue)

    def get(self):
        with self._condition:
            while self.qsize() == 0:
                self._condition.wait()
            return self._queue.pop()


class Results(object):

    def get_result_container(self):
        container = self.Container()
        return (container.set_result, container.get_result)

    class Container(object):

        def __init__(self):
            self._condition = threading.Condition()
            self._has_result = False
            self._is_exception = False
            self._result = None

        def set_result(self, result, is_exception=False):
            with self._condition:
                self._has_result = True
                self._is_exception = is_exception
                self._result = result
                self._condition.notify()

        def get_result(self):
            with self._condition:
                while not self._has_result:
                    self._condition.wait()
                if self._is_exception:
                    raise self._result
                else:
                    return self._result


class Runner(threading.Thread):

    def __init__(self, get_next_func):
        super().__init__()
        self._running = True
        self._get_next_func = get_next_func
        self._kill_lock = threading.Lock()

    def run(self):
        while self._running:
            next_func = self._get_next_func()
            self._execute(next_func)

    def running(self):
        with self._kill_lock:
            return self._running

    @staticmethod
    def pack(func, args, kwargs, set_result_func):
        return (func, args, kwargs, set_result_func)

    def _kill(self, after_stop_func):
        with self._kill_lock:
            self._running = False
            after_stop_func()

    def get_stop_call(self, set_result_func, after_stop_func):
        return (self._kill, [after_stop_func], {}, set_result_func)

    def flag_error(self, element, message='Not processed'):
        (func, args, kwargs, set_result_func) = element
        set_result_func(UnprocessedException(message), is_exception=True)

    def _execute(self, item):
        (func, args, kwargs, set_result_func) = item
        try:
            result = func(*args, **kwargs)
            set_result_func(result, is_exception=False)
        except Exception as e:
            set_result_func(e, is_exception=True)


class EventQueue(object):

    def __init__(self):
        self._queue = Queue()
        self._results = Results()
        self._runner = Runner(self._queue.get)
        self._runner.start()

    def enqueue(self, func, args=[], kwargs={}, priority_flag=False):
        set_result_func, get_result_func = self._results.get_result_container()
        item = self._runner.pack(func, args, kwargs, set_result_func)
        if self._runner.running():
            self._queue.put(item, priority_flag=priority_flag)
        else:
            self._runner.flag_error(item, "Event queue runner has stopped")
        return get_result_func

    def stop(self, priority_flag=False):
        set_result_func, get_result_func = self._results.get_result_container()
        item = self._runner.get_stop_call(set_result_func, self._flushqueue)
        self._queue.put(item, priority_flag=priority_flag)

    def _flushqueue(self):
        while self._queue.size() > 0:
            item = self._queue.get()
            self._runner.flag_error(item)
