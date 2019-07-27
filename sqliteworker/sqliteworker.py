import sqlite3
import logging
import threading
from sqliteworker.event_queue import EventQueue

LOG = logging.getLogger('sqliteworker.sqliteworker')


def select_query(cursor, query, values):
    # select is a two part instruction
    # it needs to be executed consecutively
    cursor.execute(query, values)
    return cursor.fetchall()


class SqliteWorker(EventQueue):

    def __init__(self, db_name, commit_threshold=5):
        super().__init__()
        self.db_name = db_name
        self.sentinel = object()
        self.conn = None
        self.cursor = None
        self._init()
        self.query_count = 0
        self.commit_threshold = commit_threshold
        self.running = True
        self.lock = threading.Lock()

    def __repr__(self):
        return '<%s("%s") at %s >' % (self.__class__.__name__,
                                      self.db_name, hex(id(self)))

    def _init(self):
        """Initialise sqlite3 connection and cursor
        """
        # sqlite3 objects need to be initialised in the EV runner thread
        # the python implementation lock those objects once created
        # -> unusable in other threads
        future = self.enqueue(sqlite3.connect, [self.db_name])
        self.conn = future()
        future = self.enqueue(self.conn.cursor)
        self.cursor = future()

    def execute(self, query, values=()):
        """Internal method to perform a query
        """
        # use the ? format query e.g. INSERT INTO table VALUES (?, ?)
        # it prevents from sql injections + no need to escape ?' characters
        result = None
        with self.lock:
            self.query_count += 1
        verb = query.strip().lower().split()[0]
        LOG.debug("sqlite3 run: %s %s", query, values)
        if verb.startswith('select'):
            try:
                result = self.enqueue(select_query, [self.cursor, query,
                                                     values])
            except sqlite3.Error as e:
                LOG.error('sqlite3 error: %s %s %s', query, values, e)
        else:
            try:
                result = self.enqueue(self.cursor.execute, [query, values])
            except sqlite3.Error as e:
                LOG.error('sqlite3 error: %s %s %s', query, values, e)
        return result

    def commit(self):
        try:
            LOG.debug('sqlite3 run: commit')
            future = self.enqueue(self.conn.commit)
            future()
        except sqlite3.Error as e:
            LOG.error('sqlite3 error: %s', e)

    def close(self):
        try:
            LOG.debug('sqlite3 run: close')
            future = self.enqueue(self.conn.close)
            future()
        except sqlite3.Error as e:
            LOG.error('sqlite3 error: close %s', e)

    def stop(self, priority_flag=True):
        super().stop(priority_flag=False)
        self.running = False
