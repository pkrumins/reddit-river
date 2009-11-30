#!/usr/bin/python
#
# Peteris Krumins (peter@catonmat.net)
# http://www.catonmat.net  --  good coders code, great reuse
#
# Released under GNU GPL
#
# Developed as a part of redditriver.com project
# Read how it was designed:
# http://www.catonmat.net/blog/designing-redditriver-dot-com-website
#

""" This program updates the most popular subreddit information. """

import os
import sys
import fcntl
import subreddits
from pysqlite2 import dbapi2 as sqlite

sys.path.append(sys.path[0] + '/../config')
import riverconfig as config

version = "1.0"

class Lock(object):
    """ File locking class """
    def __init__(self, file):
        self.file = file

    def lock(self):
        self.f = open(self.file, 'w+')
        try:
            fcntl.lockf(self.f.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
            return True
        except IOError, e:
            return False

def main():
    try:
        srs = subreddits.get_subreddits(pages=config.subreddit_pages)
    except subreddits.RedesignError, e:
        print >>sys.stderr, "Reddit has redesigned: %s", (e,)
        sys.exit(1)
    except subreddits.SubRedditError, e:
        print >>sys.stderr, "Serious error: %s!" % e
        sys.exit(1)

    conn = sqlite.connect(database=config.database, timeout=10)
    conn.row_factory = sqlite.Row
    cur = conn.cursor()

    insert_query = ("INSERT INTO subreddits "
                    "(reddit_name, name, description, subscribers, position) "
                    "VALUES "
                    "(:reddit_name, :name, :description, :subscribers, :position) ")

    cur.execute("SELECT count(*) FROM subreddits WHERE id > 0");  # id = 0 is reddit's front page
    sr_count = cur.fetchone()[0]
    if not sr_count:
        # no subreddits, fill the database with some
        cur.executemany(insert_query, srs)
    else:
        # update positions and subscriber count
        for subreddit in srs:
            cur.execute("SELECT id, position FROM subreddits WHERE reddit_name = :reddit_name", subreddit)
            existing_sr = cur.fetchone()
            if not existing_sr:
                # a new subreddit
                cur.execute("SELECT id FROM subreddits WHERE position = :position", subreddit)
                if cur.fetchone():
                    cur.execute("UPDATE subreddits SET position = ? WHERE position = ?",
                        (sr_count+1, subreddit['position']))
                cur.execute(insert_query, subreddit)
                sr_count += 1
            else:
                cur.execute("UPDATE subreddits SET subscribers = ? WHERE id = ?",
                    (subreddit['subscribers'], existing_sr['id']))
                if subreddit['position'] != existing_sr['position']:
                    # exchange the two subreddits
                    cur.execute("SELECT id FROM subreddits WHERE position = ?", (subreddit['position'],))
                    exchange_sr = cur.fetchone()
                    pos_query = "UPDATE subreddits SET position = ? WHERE id = ?"
                    cur.execute(pos_query, (subreddit['position'], existing_sr['id']))
                    cur.execute(pos_query, (existing_sr['position'], exchange_sr['id']))

    conn.commit()

if __name__ == "__main__":

    lock = Lock(config.lock_dir + '/update_subreddits.lock')
    if not lock.lock():
        print "I might be already running!"
        sys.exit(1)

    main()

