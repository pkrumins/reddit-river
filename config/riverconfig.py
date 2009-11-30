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

""" This module defines various config values of reddit river project """

# lock directory
#
lock_dir = '/home/pkrumins/tests/python/reddit/locks'

# path to sqlite database
#
database = '/home/pkrumins/tests/python/reddit/db/redditriver.db'

# path to mobile website autodiscovery config
#
autodisc_config = '/home/pkrumins/tests/python/reddit/config/autodisc.conf'

# number of subreddit pages to monitor for changes (used by update_subreddits.py)
#
subreddit_pages = 1

# number of story pages to monitor (used by update_stories.py)
#
story_pages = 2

# default subreddit (reddit_name) to display on the front page
#
default_subreddit = 'front_page'   # front_page is the 'reddit.com' front page

# stories per page to display on redditriver.com
#
stories_per_page = 25

