#
# cmv-archiver
# https://www.github.com/01mu/cmv-archiver
#

import urllib2
import json
import psycopg2
import time
import calendar

from datetime import datetime
from lxml import html

class CMVArchiver:
    ''' Write and update threads and get delta stats from /r/changemyview '''
    def __init__(self, db, user, pw):
        ''' Initiate with db info '''
        self.db = db
        self.user = user
        self.pw = pw
        self.BASE_URL = "https://www.reddit.com/r/changemyview/new/.json"
        self.USER_AGENT = ""

    def get_common_words(self):
        ''' Get common words for tags. Soruce: github.com/dariusk/corpora '''
        with open('common', 'r') as myfile:
            common = json.loads(myfile.read())
        self.common_words = common['commonWords'];

    def db_connect(self):
        ''' DB connection '''
        dbc = "dbname=" + self.db + " user="+ self.user + " \
            password=" + self.pw
        self.conn = psycopg2.connect(dbc)
        self.cur = self.conn.cursor()

    def check_table_exists(self, table):
        ''' Check if a table exists '''
        c = "select exists(select * from information_schema.tables where \
            table_name=%s)"
        self.cur.execute(c, (table,))
        self.conn.commit()
        return self.cur.fetchall()[0][0]

    def create_table(self):
        ''' Create tables if they don't exist '''
        if not self.check_table_exists('posts'):
            self.cur.execute('''CREATE TABLE posts
                (ID SERIAL PRIMARY KEY,
                TITLE TEXT NOT NULL,
                OP TEXT NOT NULL,
                URL TEXT NOT NULL,
                COMMENTS INT NOT NULL,
                DELTA BOOL NOT NULL,
                SCORE INT NOT NULL,
                DATE INT NOT NULL);''')
            self.conn.commit()
            print("TABLE CREATED: posts")

        if not self.check_table_exists('stats'):
            self.cur.execute(''' CREATE TABLE stats
                (ID SERIAL PRIMARY KEY,
                VALUE TEXT NOT NULL,
                KEY TEXT NOT NULL);''')
            self.conn.commit()
            print("TABLE CREATED: stats")

    def get_page(self, limit, after):
        ''' Get reddit page from API with pagination '''
        url = self.BASE_URL + '?limit=' + str(limit) + '&after=' + after
        request = urllib2.Request(url)
        request.add_header('User-Agent', self.USER_AGENT)
        data = urllib2.urlopen(request).read()
        self.json = json.loads(data)

    def update_posts(self):
        ''' Iterate through posts and insert or update '''
        after = ""
        self.get_page(100, "")

        while after != None:
            for i in range(len(self.json['data']['children'])):
                child = self.json['data']['children'][i]['data']
                title = str(child['title'].encode('utf-8').strip())
                flair = self.check_delta(str(child['link_flair_text']))
                comments = child['num_comments']
                score = child['score']
                url = str(child['url'].encode('utf-8').strip())
                op = str(child['selftext'].encode('utf-8').strip())
                date = child['created_utc']

                check_query = "SELECT ID FROM POSTS WHERE URL = %s"
                check_arr = (url,)
                check = self.check_exists(check_query, check_arr)

                if not (check):
                    query = "INSERT INTO POSTS \
                        (TITLE, OP, URL, COMMENTS, DELTA, SCORE, DATE) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    vals = (title, op, url, comments, flair, score, date)
                    print("INSERTED: " + title)
                else:
                    query = "UPDATE POSTS \
                        SET TITLE = %s, OP = %s, URL = %s, COMMENTS = %s, \
                        DELTA = %s, SCORE = %s, DATE = %s WHERE URL = %s"
                    vals = (title, op, url, comments, flair,
                        score, date, url)
                    print("UPDATED: " + title)

                self.cur.execute(query, vals)
                self.conn.commit()

            after = self.json['data']['after']

            if not after == None:
                self.get_page(100, after)
            else:
                break

    def update_stats(self):
        ''' Update post stats '''
        tp_query = "SELECT COUNT(ID) FROM POSTS"
        false_query = "SELECT COUNT(ID) FROM POSTS WHERE DELTA = 'False'"
        true_query = "SELECT COUNT(ID) FROM POSTS WHERE DELTA = 'True'"
        score_query = "SELECT SUM(SCORE) FROM POSTS"
        fscore_query = "SELECT SUM(SCORE) FROM POSTS WHERE DELTA = 'False'"
        tscore_query = "SELECT SUM(SCORE) FROM POSTS WHERE DELTA = 'True'"
        cmts_query = "SELECT SUM(COMMENTS) FROM POSTS"
        fcmts_query = "SELECT SUM(COMMENTS) FROM POSTS WHERE DELTA = 'False'"
        tcmts_query = "SELECT SUM(COMMENTS) FROM POSTS WHERE DELTA = 'True'"

        total_posts = self.get_value(tp_query, ())
        false_posts = self.get_value(false_query, ())
        true_posts = self.get_value(true_query, ())
        score_total = self.get_value(score_query, ())
        fscore_total = self.get_value(fscore_query, ())
        tscore_total = self.get_value(tscore_query, ())
        cmts_total = self.get_value(cmts_query, ())
        fcmts_total = self.get_value(fcmts_query, ())
        tcmts_total = self.get_value(tcmts_query, ())

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
        key = 'first_update'
        first_update = calendar.timegm(datetime.utcnow().utctimetuple())

        check = self.check_exists("SELECT ID FROM STATS WHERE key = %s", (key,))

        if not check:
            query = "INSERT INTO STATS (KEY, VALUE) VALUES (%s, %s)"
            vals = (key, first_update)
            print("STATS INSERTED: " + key + " " + str(first_update))
            self.cur.execute(query, vals)
            self.conn.commit()

    def update_value(self, key, value):
        ''' Update a given stats value from DB '''
        check = self.check_exists("SELECT ID FROM STATS WHERE key = %s", (key,))

        if not check:
            query = "INSERT INTO STATS (KEY, VALUE) VALUES (%s, %s)"
            vals = (key, value)
            print("STATS INSERTED: " + key + " " + str(value))
        else:
            query = "UPDATE STATS SET KEY = %s, VALUE = %s WHERE key = %s"
            vals = (key, value, key)
            print("STATS UPDATED: " + key + " " + str(value))

        self.cur.execute(query, vals)
        self.conn.commit()

    def get_value(self, query, vals):
        ''' Get stats value from query '''
        self.cur.execute(query, vals)
        return self.cur.fetchall()[0][0]

    def check_delta(self, flair):
        ''' Check if delta appears in title flair '''
        return flair.find("elta") >= 0

    def check_exists(self, query, vals):
        ''' Check if topic exists in DB '''
        self.cur.execute(query, vals)
        rows = self.cur.fetchall()
        self.conn.commit()
        return len(rows) > 0

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
