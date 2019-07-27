import sqlite3
import unittest

from sqliteworker.sqliteworker import SqliteWorker


class TestSqliteworker(unittest.TestCase):

    def setUp(self):
        self.worker = SqliteWorker(':memory:')

    def tearDown(self):
        self.worker.stop()

    def test_insert_select(self):
        res = self.worker.execute('''CREATE TABLE stocks
             (date text, symbol text, price real)''')
        res()
        res = self.worker.execute('''INSERT INTO stocks
            VALUES (?, ?, ?)''', ('2019', 'TSLA', 228.04))
        res()
        self.worker.commit()
        res = self.worker.execute('''SELECT * FROM stocks''')
        res = res()
        self.assertEqual(res, [('2019', 'TSLA', 228.04)])

    def test_query_error(self):
        res = self.worker.execute('not a query')
        with self.assertRaises(sqlite3.Error):
            res()
