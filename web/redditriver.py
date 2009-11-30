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


import web
import sys
import re

from datetime import datetime, timedelta
from time import mktime
from urlparse import urlparse

sys.path.append(sys.path[0] + '/../config')

import riverconfig as config

urls = (
    '/',                                 'RedditRiver',
    '/page/(\d+)/?',                     'RedditRiverPage',
    '/r/([a-zA-Z0-9_.-]+)/?',            'SubRedditRiver',
    '/r/([a-zA-Z0-9_.-]+)/page/(\d+)/?', 'SubRedditRiverPage',
    '/reddits/?',                        'SubReddits',
    '/stats/?',                          'Stats',
    '/stats/([a-zA-Z0-9_.-]+)/?',        'SubStats',
    '/about/?',                          'AboutRiver'
)

web.webapi.internalerror = web.debugerror
web.config.db_parameters = dict(dbn='sqlite', db=config.database)

# no escaping needs to be done as the data we get from reddit is already escaped
web.net.htmlquote = lambda x: x

def get_nice_host(url):
    """ Given a URL, extracts a 'nice' version of host, for example:
        >>> get_nice_host('http://www.reddit.com') 
        'reddit.com'
        >>> get_nice_host('http://ww2.nba.com') 
        'nba.com'
        >>> get_nice_host('http://foo.bar.baz/a.html') 
        'foo.bar.baz' """

    parsed_url = urlparse(url)
    host = parsed_url[1] # 1 is 'host'
    host = re.sub(r'www?\d*\.', '', host)
    return host

class Stories(object):
    def __init__(self, subreddit, page):
        self.subreddit = subreddit
        self.page = int(page)
        if self.page == 0: self.page = 1
        if self.page > sys.maxint: self.page = 1

    def _story_query(self):
        story_query = ("SELECT st.title title, st.url url, st.url_mobile url_mobile, "
                       "st.score score, st.comments comments, st.user user, "
                       "st.date_reddit date_reddit "
                       "FROM stories st "
                       "LEFT JOIN subreddits su "
                       "ON st.subreddit_id = su.id "
                       "WHERE su.reddit_name = '%s' "
                       "ORDER BY st.position, st.date_added DESC "
                       "LIMIT %d "
                       "OFFSET %d")

        offset = (self.page - 1) * config.stories_per_page

        # We do a trick here of making a query for + 1 story to see if we
        # should display the next page link. If we get +1 story, then
        # the next page exists.
        #
        query = (story_query % (self.subreddit, config.stories_per_page + 1, offset))
        return query

    def get(self):
        query = self._story_query()
        tmp_stories = web.query(query)

        stories = []
        next_page = prev_page = False
        for idx, s in enumerate(tmp_stories):
            if idx >= config.stories_per_page:
                next_page = True
                break
            s.host = get_nice_host(s['url'])
            s.niceago = web.datestr(datetime.fromtimestamp(s['date_reddit']), datetime.now())
            stories.append(s)

        if self.page != 1:
            prev_page = True

        next_page_link = prev_page_link = None
        if next_page:
            next_page_link = self.next_page(self.subreddit, self.page)
        if prev_page:
            prev_page_link = self.prev_page(self.subreddit, self.page)

        return {'stories': stories,
                'next_page': next_page,
                'prev_page': prev_page,
                'next_page_link': next_page_link,
                'prev_page_link': prev_page_link}


class RiverStories(Stories):
    def __init__(self, page=1):
        super(RiverStories, self).__init__(config.default_subreddit, page)

    def next_page(self, subreddit, page):
        return "/page/" + str(page + 1)

class RiverStoriesPage(RiverStories):
    def __init__(self, page):
        super(RiverStoriesPage, self).__init__(page)

    def prev_page(self, subreddit, page):
        if page == 2: return "/"
        return "/page/" + str(page - 1)

class SubRiverStories(Stories):
    def __init__(self, subreddit, page=1):
        super(SubRiverStories, self).__init__(subreddit, page)

    def next_page(self, subreddit, page):
        return "/r/" + subreddit + "/page/" + str(page + 1)

class SubRiverStoriesPage(SubRiverStories):
    def __init__(self, subreddit, page):
        super(SubRiverStoriesPage, self).__init__(subreddit, page)

    def prev_page(self, subreddit, page):
        if page == 2:
            return "/r/" + subreddit 
        return "/r/" + subreddit + "/page/" + str(page - 1)

class UserStats(object):
    def __init__(self, subreddit=config.default_subreddit, count=10):
        self.subreddit = subreddit
        self.count = count

    def _user_query(self):
        stats_query = ("SELECT COUNT(st.user) stories, st.user user "
                       "FROM stories st "
                       "LEFT JOIN subreddits su "
                       "ON st.subreddit_id = su.id "
                       "WHERE su.reddit_name = '%s' "
                       "GROUP BY user "
                       "ORDER BY stories DESC "
                       "LIMIT %d ")

        query = stats_query % (self.subreddit, self.count)
        return query

    def get(self):
        query = self._user_query()
        users = web.query(query)
        return users

class StoryStats(object):
    def __init__(self, time_offset, subreddit=config.default_subreddit, count=10):
        self.subreddit = subreddit
        self.count = count
        self.time_offset = time_offset

    def _story_query(self):
        stats_query = ("SELECT st.title title, st.url url, st.url_mobile url_mobile, "
                       "st.score score, st.comments comments, st.user user, "
                       "st.date_reddit date_reddit "
                       "FROM stories st "
                       "LEFT JOIN subreddits su "
                       "ON st.subreddit_id = su.id "
                       "WHERE su.reddit_name = '%s' AND st.date_reddit >= %d "
                       "ORDER BY st.score DESC "
                       "LIMIT %d ")

        query = stats_query % (self.subreddit, self.time_offset, self.count)
        return query

    def get(self):
        query = self._story_query()
        tmp_stories = web.query(query)
        stories = []
        for s in tmp_stories:
            s.host = get_nice_host(s['url'])
            s.niceago = web.datestr(datetime.fromtimestamp(s['date_reddit']), datetime.now())
            stories.append(s)
        return stories


################
# page handlers
################

class RedditRiver(object):
    def GET(self):
        st = RiverStories()
        story_page = st.get()
        web.render('stories.tpl.html', story_page)

class RedditRiverPage(object):
    def GET(self, page):
        st = RiverStoriesPage(page)
        story_page = st.get()
        web.render('stories.tpl.html', story_page)

class SubRedditRiver(object):
    def GET(self, subreddit):
        st = SubRiverStories(subreddit)
        story_page = st.get()
        story_page['subreddit'] = subreddit
        web.render('stories.tpl.html', story_page)

class SubRedditRiverPage(object):
    def GET(self, subreddit, page):
        st = SubRiverStoriesPage(subreddit, page)
        story_page = st.get()
        story_page['subreddit'] = subreddit
        web.render('stories.tpl.html', story_page)

class SubReddits(object):
    def GET(self):
        subreddits = web.query("SELECT * FROM subreddits WHERE id > 0 and active = 1 ORDER by position")
        web.render('subreddits.tpl.html')

class AboutRiver(object):
    def GET(self):
        about = True
        web.render('about.tpl.html')

class Stats(object):
    def GET(self):
        user_stats = UserStats(count=10).get()
        
        week_ago = datetime.now() - timedelta(days=7)
        unix_week = int(mktime(week_ago.timetuple()))
        story_stats = StoryStats(time_offset = unix_week, count=15).get()
        web.render('stats.tpl.html', {'user_stats': user_stats, 'story_stats': story_stats})

class SubStats(object):
    def GET(self, subreddit):
        user_stats = UserStats(subreddit, count=10).get()

        week_ago = datetime.now() - timedelta(days=7)
        unix_week = int(mktime(week_ago.timetuple()))
        story_stats = StoryStats(time_offset = unix_week, subreddit=subreddit, count=15).get()
        web.render('stats.tpl.html', {'user_stats': user_stats, 'story_stats': story_stats,
            'subreddit': subreddit})

if __name__ == "__main__":
    web.run(urls, globals(), web.reloader)

