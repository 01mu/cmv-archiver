# cmv-archiver
Get thread info, statistics, and delta info from reddit's /r/changemyview. Writes posts to a PostgreSQL database.
## Usage
```python
from cmv_archiver import CMVArchiver

psql_db = ""
psql_user = ""
psql_pw = ""

cmv_archiver = CMVArchiver(psql_db, psql_user, psql_pw)
cmv_archiver.db_connect()
cmv_archiver.create_table()
cmv_archiver.update_posts()
cmv_archiver.update_stats()
```
```
INSERTED: <thread title>
UPDATED: <thread title>
UPDATED: <thread title>
...
STATS UPDATED: total_posts 984
STATS UPDATED: false_posts 490
STATS UPDATED: true_posts 494
STATS UPDATED: false_per 49.8
STATS UPDATED: true_per 50.2
STATS UPDATED: last_update 1540499783
...
```
