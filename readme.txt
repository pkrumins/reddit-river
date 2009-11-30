This is the redditriver.com website that I created back in 2008. The route to
university took 30 mins and during this time I didn't have much else to do than
to read reddit. But the orginal website didn't look well under my cellphone's
browser so I created redditriver that was more mobile friendly.

Read the whole story on how it was designed at:

    http://catonmat.net/blog/designing-redditriver-dot-com-website

-----------------------------------------------------------------------------

Here is the description of directories in the source tree:

bin - python modules and executables for retrieving reddit stories,
      subreddits, finding mobile versions of web pages, and updating
      the retrieved data in the database

      autodiscovery.py     - discovers mobile versions of web pages
      redditstories.py     - retrieves reddit stories on front page or
                             any given subreddit
      subreddits.py        - retrieves the most popular subreddits
      update_stories.py    - updates stories in the database
      update_subreddits.py - updates subreddits in the database

config - configuration files of redditriver.com website, tools and
         autodiscovery.py program

         autodisc.conf  - configuration file of bin/autodiscovery.py program
         riverconfig.py - configuration module for bin/update_stories.py,
                          bin/update_subreddits.py, bin/autodiscovery.py,
                          and web/redditriver.py

db - example sqlite database with 25 subreddits and around 50 stories for
     each subreddit, and database schema file.

     redditriver.sb - sqlite3 database with 1351 records in stories table and
                      26 records in subreddits table
     db.schema.txt  - database sql shema

html.examples - contains html page fragments of stories, scores,
                subreddits and next pages of reddit.com. these were used for
                programming data extractors bin/update_stories.py and
                bin/update_subreddits.py
              
                score.txt - html code of
                                     http://reddit.com/info/reddit_id/details
                story.txt - html code of a single story on reddit front
                            page or any subreddit.
                subreddit.entry.txt - html code of a subreddit entry at
                                      http://reddit.com/reddits
                subreddit.next.page.txt - html code of next page <a> link

locks - directory containing lock files, used by bin/update_stories.py and
        bin/update_subreddits.py

web - the redditriver.com python website/application!!!

      redditriver.py - application using web.py to serve the contents of the
                       website

      static - static content of the website, such as favicon.ico,
               website logo, my photo with reddit t-shirt and css stylesheet.

templates - templates used by redditriver.py. these get rendered by cheetah's
            template engine!

-----------------------------------------------------------------------------

Copyright (C) 2008 Peteris Krumins (peter@catonmat.net)
http://www.catonmat.net  -  good coders code, great reuse

Released under GNU GPL license.

------------------------------------------------------------------------------

Sincerely,
Peteris Krumins
http://www.catonmat.net

