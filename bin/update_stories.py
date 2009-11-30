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

""" This program updates the latest story list """

import os
import sys
import time
import fcntl
import redditstories
import autodiscovery
from itertools import izip, count
from pysqlite2 import dbapi2 as sqlite

sys.path.append(sys.path[0] + '/../config')

import riverconfig as config

version = "1.0"

class Lock(object):
    """ File locking class """
    def __init__(self, file):
        self.file = file

    def lock(self):
        self.f = open(self.file, 'w')
        try:
            fcntl.lockf(self.f.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
            return True
        except IOError, e:
            return False

# Whether to do autodiscovery (when testing sometimes it's not needed)
# Can be set to false with --noautodisc command option
do_autodiscovery = True

# Wheter to print autodiscovery information
# Can be set to true with --autodescdebug command option
autodiscdebug = False

# This program keeps track of story positions accross config.story_pages reddit pages.
# If the story is no longer found in these pages, the information about its
# position on reddit is lost, and it is assigned an infinity position.
#
# How big is infinity? Suppose that there are 10000 new stories on reddit daily which
# hit the front page. If the infinity is a billion (1000000000), then it would take
# 1000000000 / 10000 = 100000 days or 273 years to overflow this number.
# 
infinity_position = 1000000000

def main():
    conn = sqlite.connect(database=config.database, timeout=10)
    conn.row_factory = sqlite.Row
    cur = conn.cursor()
    
    cur.execute("SELECT id, reddit_name FROM subreddits WHERE active = 1")
    subreddits = cur.fetchall()

    total_new = 0
    total_updated = 0
    for subreddit in subreddits:
        new_stories = 0
        updated_stories = 0
        print "Going after %s's subreddit stories! " % subreddit['reddit_name']
        try:
            stories = redditstories.get_stories(subreddit=subreddit['reddit_name'], pages=config.story_pages)
        except redditstories.RedesignError, e:
            print "Could not get stories for %s (reddit might have redesigned: %s)!" % (subreddit['reddit_name'], e)
            continue
        except redditstories.StoryError, e:
            print "Serious error while getting %s: %s!" % (subreddit['reddit_name'], e)
            continue

        for position, story in izip(count(1), stories):
            story['position'] = position
            story['subreddit_id'] = subreddit['id']
            cur.execute("SELECT id, position FROM stories WHERE subreddit_id = ? AND title = ? AND url = ?",
                (subreddit['id'], story['title'], story['url']))
            existing_row = cur.fetchone()
            if existing_row:
                updated_stories += 1
                cur.execute("UPDATE stories SET score = ?, comments = ? WHERE id = ?",
                    (story['score'], story['comments'], existing_row['id']))
                if existing_row['position'] != story['position']:
                    # swap both positions to maintain consistency of positions
                    swap_id = cur.execute("SELECT id FROM stories WHERE subreddit_id = ? AND position = ?",
                        (subreddit['id'], position)).fetchone()[0]
                    cur.execute("UPDATE stories SET position = ? WHERE id = ?",
                        (story['position'], existing_row['id'])) 
                    cur.execute("UPDATE stories SET position = ? WHERE id = ?",
                        (existing_row['position'], swap_id))
                    conn.commit()
                continue

            story['url_mobile'] = ""
            if do_autodiscovery:
                try:
                    if autodiscdebug:
                        print "Autodiscovering '" + story['url'] + "'"
                    autodisc = autodiscovery.AutoDiscovery()
                    story['url_mobile'] = autodisc.autodiscover(story['url'])
                    if autodiscdebug:
                        if story['url_mobile']:
                            print "Autodiscovered '" + story['url_mobile'] + "'"
                        else:
                            print "Did not autodiscover anything!"
                except (autodiscovery.AutoDiscoveryError, UnicodeEncodeError), e:
                    if autodiscdebug:
                        print "Failed autodiscovering: %s" % e
                    pass

            story['date_added'] = int(time.time())

            story_at_pos = cur.execute("SELECT id FROM stories WHERE subreddit_id = ? AND position = ?",
                (subreddit['id'], position)).fetchone()
            if story_at_pos:
                id = story_at_pos[0]
                cur.execute("UPDATE stories SET position = ? WHERE id = ?", (infinity_position, id))
            
            cur.execute("INSERT INTO stories (title, url, url_mobile, reddit_id, subreddit_id, "
                        "score, comments, user, position, date_reddit, date_added) "
                        "VALUES (:title, :url, :url_mobile, :id, :subreddit_id, :score, "
                        ":comments, :user, :position, :unix_time, :date_added)",
                        story)
            new_stories += 1
            conn.commit()

        total_new += new_stories
        total_updated += updated_stories
        print "%d new and %d updated (%d total)" % (new_stories, updated_stories, new_stories + updated_stories)

    print "Total: %d new and %d updated (%d total)" % (total_new, total_updated, total_new + total_updated)

if __name__ == "__main__":
    lock = Lock(config.lock_dir + '/update_stories.lock')
    if not lock.lock():
        print "I might be already running!"
        sys.exit(1)

    argv = sys.argv[1:]
    if "--noautodisc" in argv:
        print "Setting autodiscovery to False"
        do_autodiscovery = False
    if "--autodiscdebug" in argv:
        print "Setting autodiscovery debug to True"
        autodiscdebug = True

    main()

