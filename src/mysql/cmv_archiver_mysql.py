#
# cmv-archiver
# github.com/01mu
#

import urllib2
import json
import psycopg2
import time
import calendar
import MySQLdb

from datetime import datetime
from lxml import html

class CMVArchiver:
    ''' Write and update threads and get delta stats from /r/changemyview '''
    def __init__(self, db, user, pw, socket):
        ''' Initiate with db info '''
        self.socket = socket
        self.db = db
        self.user = user
        self.pw = pw
        self.BASE_URL = "https://www.reddit.com/r/changemyview/new/.json"
        self.USER_AGENT = ""

    def get_common_words(self):
        ''' Get common words for tags. Soruce: github.com/dariusk/corpora '''
        with open('../../res/common', 'r') as myfile:
            common = json.loads(myfile.read())
        self.common_words = common['commonWords'];

    def db_connect(self):
        ''' DB connection '''
        if len(self.socket) > 0:
            self.db = MySQLdb.connect(unix_socket = self.socket,
                user = self.user, passwd = self.pw, db = self.db)
        else:
            self.db = MySQLdb.connect(user = self.user, passwd = self.pw,
                db = self.db)

        self.cur = self.db.cursor()

    def check_table_exists(self, table):
        ''' Check if a table exists '''
        sql = "SHOW TABLES LIKE '" + table + "'"
        self.cur.execute(sql)
        results = self.cur.fetchall()

        return len(results) > 0

    def create_table(self):
        ''' Create tables if they don't exist '''
        if not self.check_table_exists('posts'):
            sql = "CREATE TABLE posts ( \
                id  int(8) NOT NULL AUTO_INCREMENT, \
                title longtext, \
                op longtext, \
                url longtext, \
                comments int(8), \
                delta varchar(255), \
                score int(8), \
                date int(8), \
                last_update int(8), \
                PRIMARY KEY (id))"

            self.cur.execute(sql)
            self.db.commit()
            print("TABLE CREATED: posts")

        if not self.check_table_exists('stats'):
            sql = "CREATE TABLE stats ( \
                id int(8) NOT NULL AUTO_INCREMENT, \
                value varchar(255), \
                input varchar(255), \
                PRIMARY KEY (id))"

            self.cur.execute(sql)
            self.db.commit()
            print("TABLE CREATED: stats")

    def get_page(self, limit, after):
        ''' Get reddit page from API with pagination '''
        url = self.BASE_URL + '?limit=' + str(limit) + '&after=' + after
        request = urllib2.Request(url)
        request.add_header('User-Agent', self.USER_AGENT)
        data = urllib2.urlopen(request).read()
        self.json = json.loads(data)

    def check_title(self, title_text):
        if title_text.find("CMV: ") >= 0:
            strip = title_text.replace("CMV: ", "")
        else:
            strip = "bad"

        return strip

    def update_posts(self):
        ''' Iterate through posts and insert or update '''
        after = ""
        self.get_page(100, "")

        while after != None:
            for i in range(len(self.json['data']['children'])):
                child = self.json['data']['children'][i]['data']

                title_text = str(child['title'].encode('utf-8').strip())
                title = self.check_title(title_text)

                if title == "bad":
                    continue

                op = str(child['selftext'].encode('utf-8').strip())
                flair = self.check_delta(str(child['link_flair_text']))
                comments = int(child['num_comments'])
                score = int(child['score'])
                url = str(child['url'].encode('utf-8').strip())
                date = int(child['created_utc'])

                last_update = calendar.timegm(datetime.utcnow().utctimetuple())

                check_query = "SELECT id FROM posts WHERE URL = '%s'"
                check_arr = (url)
                check = self.check_exists(check_query, check_arr)

                if not (check):
                    sql = "INSERT INTO posts (title, op, url, comments, \
                        delta, score, date, last_update) VALUES (%s, %s, %s, \
                        %s, %s, %s, %s, %s)"
                    vals = (title, op, url, comments, flair, score,
                        date, last_update)
                    print("INSERTED: " + title)
                else:
                    sql = "UPDATE posts SET title = %s, op = %s, url = %s, \
                        comments = %s, delta = %s, score = %s, date = %s, \
                        last_update = %s WHERE url = %s"
                    vals = (title, op, url, comments, flair, score,
                        date, last_update, url)
                    print("UPDATED: " + title)

                self.cur.execute(sql, vals)
                self.db.commit()

            after = self.json['data']['after']

            if not after == None:
                self.get_page(100, after)
            else:
                break

    def update_stats(self):
        ''' Update post stats '''
        tp_query = "SELECT COUNT(id) FROM posts"
        false_query = "SELECT COUNT(id) FROM posts WHERE delta = False"
        true_query = "SELECT COUNT(id) FROM posts WHERE delta = True"
        score_query = "SELECT SUM(score) FROM posts"
        fscore_query = "SELECT SUM(score) FROM posts WHERE delta = False"
        tscore_query = "SELECT SUM(score) FROM posts WHERE delta = True"
        cmts_query = "SELECT SUM(comments) FROM posts"
        fcmts_query = "SELECT SUM(comments) FROM posts WHERE delta = False"
        tcmts_query = "SELECT SUM(comments) FROM posts WHERE delta = True"

        total_posts = float(self.get_value(tp_query, ()))
        false_posts = float(self.get_value(false_query, ()))
        true_posts = float(self.get_value(true_query, ()))
        score_total = float(self.get_value(score_query, ()))
        fscore_total = float(self.get_value(fscore_query, ()))
        tscore_total = float(self.get_value(tscore_query, ()))
        cmts_total = float(self.get_value(cmts_query, ()))
        fcmts_total = float(self.get_value(fcmts_query, ()))
        tcmts_total = float(self.get_value(tcmts_query, ()))

        false_per = round(float(false_posts) / total_posts * 100, 2)
        true_per = round(float(true_posts) / total_posts * 100, 2)

        fscore_per = round(float(fscore_total) / score_total * 100, 2)
        tscore_per = round(float(tscore_total) / score_total * 100, 2)

        fcmts_per = round(float(fcmts_total) / cmts_total * 100, 2)
        tcmts_per = round(float(tcmts_total) / cmts_total * 100, 2)

        last_update = calendar.timegm(datetime.utcnow().utctimetuple())

        updates = [("total_posts", total_posts), ("false_posts", false_posts),
            ("true_posts", true_posts), ("false_per", false_per),
            ("true_per", true_per), ("last_update", last_update),
            ("score_total", score_total), ("fscore_total", fscore_total),
            ("tscore_total", tscore_total), ("fscore_per", fscore_per),
            ("tscore_per", tscore_per), ("cmts_total", cmts_total),
            ("fcmts_total", fcmts_total), ("tcmts_total", tcmts_total),
            ("fcmts_per", fcmts_per), ("tcmts_per", tcmts_per)]

        for i in range(len(updates)):
            self.update_value(updates[i][0], updates[i][1])

        self.first_update()

    def first_update(self):
        ''' Get time of first update '''
        value = 'first_update'
        first_update = calendar.timegm(datetime.utcnow().utctimetuple())
        check = self.check_exists("SELECT id FROM stats WHERE value = '%s'",
            (value))

        if not check:
            vals = (first_update, value)
            sql = "INSERT INTO stats (value, input) VALUES (%s, %s)"
            self.cur.execute(sql, vals)
            self.db.commit()
            print("STATS INSERTED: " + value + " " + str(first_update))

    def update_value(self, input, value):
        ''' Update a given stats value from DB '''
        check = self.check_exists("SELECT id FROM stats WHERE input = '%s'",
            (input))

        if not check:
            query = "INSERT INTO stats (input, value) VALUES (%s, %s)"
            vals = (input, value)
            print("STATS INSERTED: " + input + " " + str(value))
        else:
            query = "UPDATE stats SET input = %s, value = %s WHERE input = %s"
            vals = (input, value, input)
            print("STATS UPDATED: " + input + " " + str(value))

        self.cur.execute(query, vals)
        self.db.commit()

    def get_value(self, query, vals):
        self.cur.execute(query % vals)
        results = self.cur.fetchall()

        for row in results:
            val = row[0]

        return val

    def check_delta(self, flair):
        ''' Check if delta appears in title flair '''
        return flair.find("elta") >= 0

    def check_exists(self, query, vals):
        self.cur.execute(query % vals)
        results = self.cur.fetchall()
        return len(results) > 0

    def get_tags(self, op):
        ''' Get most mentioned words in OP excluding common words '''
        from collections import Counter

        tags = ""
        split = op.split()
        Counter = Counter(split)
        occur = Counter.most_common(20)

        for i in range(len(occur)):
            word = occur[i][0]

            if not word in self.common_words:
                tags = tags + " " + word

        print(tags)
        return tags
