#
# cmv-archiver
# https://www.github.com/01mu/cmv-archiver
#

from cmv_archiver import CMVArchiver

psql_db = ""
psql_user = ""
psql_pw = ""

cmv_archiver = CMVArchiver(psql_db, psql_user, psql_pw)
cmv_archiver.db_connect()
cmv_archiver.create_table()
cmv_archiver.update_posts()
cmv_archiver.update_stats()
