import os
import queue
import requests
import threading
import logging
from sqliteworker.sqliteworker import SqliteWorker

logging.basicConfig(level='INFO')
LOG = logging.getLogger('get_urls')

N_WORKERS = 4
HTTP_TIMEOUT = 5
SENTINEL = object()

fname = 'urllist.txt'
dirname = os.path.dirname(os.path.abspath(__file__))
fname = os.path.join(dirname, fname)
with open(fname, 'r') as f:
    urls = f.read().splitlines()

work_queue = queue.Queue()
for url in urls:
    work_queue.put(url)

db = SqliteWorker(':memory:')
db.execute('''CREATE TABLE urls
    (url TEXT PRIMARY KEY, status_code INT)''')
db.commit()


def get_url(work_queue):
    http_session = requests.Session()
    for url in iter(work_queue.get, SENTINEL):
        try:
            LOG.info('%s', url)
            resp = http_session.head(url, timeout=HTTP_TIMEOUT)
            db.execute('''INSERT INTO urls (url, status_code)
                VALUES (?, ?)''', (url, resp.status_code))
        except Exception as e:
            LOG.error('%s', e)


workers = []
for n in range(N_WORKERS):
    work_queue.put(SENTINEL)
    t = threading.Thread(target=get_url, args=(work_queue,))
    t.start()
    workers.append(t)


for t in workers:
    t.join()

db.commit()

future = db.execute('''SELECT * FROM urls''')
results = future()
if not results:
    print('no results')
else:
    print('\nresults:\n')
    for result in results:
        print(result)

db.close()
db.stop()
