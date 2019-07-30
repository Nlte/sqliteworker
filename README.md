# Multithreaded sqlite worker

Thread safe class to interact with sqlite databases in python.
The class encapsulates a sqlite connection / cursor. Externals threads submit queries to the sqlite worker. Those queries are pushed to an event queue which runs them on the sqlite database and returns a future.

## Usage
```
from sqliteworker.sqliteworker import SqliteWorker

w = SqliteWorker(':memory:')

w.execute('''CREATE TABLE stocks
             (date text, trans text, symbol text, qty real, price real)''')

# Insert a row of data
values = ('2006-01-05','BUY','RHAT',100,35.14)
w.execute("INSERT INTO stocks VALUES (?,?,?,?,?)", values)

# Commit the changes
w.commit()

# Query the stocks table
future = w.execute('''SELECT * FROM stocks''')
result = future()
print(result)

# Close / stop worker
w.close()
w.stop()
```

## Installing
No external dependencies, it uses only the standard python3 library.
```
make install
```

## Running the tests
```
make test
```

