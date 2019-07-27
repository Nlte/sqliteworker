import unittest

from sqliteworker.event_queue import Queue, Results, EventQueue


class TestQueue(unittest.TestCase):

    def setUp(self):
        self.myqueue = Queue()

    def test_init(self):
        self.assertEqual(len(self.myqueue._queue), 0)

    def test_priority(self):
        self.myqueue.put(1, False)
        self.myqueue.put(2, priority_flag=True)
        res = self.myqueue.get()
        self.assertEqual(res, 2)


class TestResults(unittest.TestCase):

    def setUp(self):
        res = Results()
        funcs = res.get_result_container()
        self.set_func, self.get_func = funcs

    def test_result(self):
        self.set_func('abcd', is_exception=False)
        res = self.get_func()
        self.assertEqual(res, 'abcd')

    def test_result_exception(self):
        self.set_func(ValueError('abcd'), is_exception=True)
        with self.assertRaises(ValueError):
            res = self.get_func()
            res()


class TestEventQueue(unittest.TestCase):

    def setUp(self):
        self.ev = EventQueue()

    def tearDown(self):
        self.ev.stop()

    def test_ev_result(self):
        def test_func():
            return 5
        res = self.ev.enqueue(test_func)
        res = res()
        self.assertEqual(res, 5)

    def test_ev_exception(self):
        def test_func():
            raise ValueError('abcd')
        res = self.ev.enqueue(test_func)
        with self.assertRaises(ValueError):
            res = res()

    def test_args_kwargs(self):
        def test_func(*args, **kwargs):
            return args, kwargs
        res = self.ev.enqueue(test_func, ['a', 'b'], kwargs={'x': 1})
        args, kwargs = res()
        self.assertEqual(args, ('a', 'b'))
        self.assertEqual(kwargs, {'x': 1})

        def add_func(n):
            return n + 2

        res = self.ev.enqueue(add_func, [1])
        res = res()
        self.assertEqual(res, 3)


if __name__ == '__main__':
    unittest.main()
