#
# cmv-archiver
# github.com/01mu
#

from cmv_archiver_mysql import CMVArchiver

db = ""
user = ""
pw = ""
socket = ""

cmv_archiver = CMVArchiver(db, user, pw, socket)
cmv_archiver.db_connect()
cmv_archiver.create_table()
cmv_archiver.update_posts()
cmv_archiver.update_stats()
