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

"""
This module autodiscovers a print or mobile version
of a page at a given URL.

Throws an AutoDiscoveryError in case of a fatal error.
"""

import re
import sys
import socket
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup, NavigableString

sys.path.append(sys.path[0] + '/../config')
import riverconfig as config

socket.setdefaulttimeout(15)

version = "1.0"

class AutoDiscoveryError(Exception):
    """ Exception which this module might throw. """
    pass

class AutoDiscovery(object):
    """ Autodiscovers URL of a mobile version of a webpage. """

    dispatchers = None

    def __init__(self, config_file=config.autodisc_config):
        self.lookups = []
        self.rewriters = []
        self.ignores = []
        if AutoDiscovery.dispatchers is None:
            self._init_dispatchers()
        self._parse_config(config_file)

    def _init_dispatchers(self):
        """ Inits dispatcher config directive dispatcher table. """

        AutoDiscovery.dispatchers = {
            'PRINT_LINK': AutoDiscovery._print_link,
            'REWRITE_URL': AutoDiscovery._rewrite_url,
            'IGNORE_URL': AutoDiscovery._ignore_url
        }

    def _parse_config(self, config_file):
        """
        Parses the config and populates self.lookups list with functions
        which get called on the page to find mobile friendly version of the
        site at url.
        """

        try:
            file = open(config_file, 'r')
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    command, data = re.split(r'\s+|\t+', line, 1)
                except ValueError:
                    raise AutoDiscoveryError, ("Unknown line: '%s' while parsing '%s'" % (line, config_file))
                
                if command not in AutoDiscovery.dispatchers:
                    raise AutoDiscoveryError, "Config command '%s' not found" % command

                AutoDiscovery.dispatchers[command](self, data)
            file.close()
        except IOError, e:
            raise AutoDiscoveryError, e

    def _print_link(self, data):
        """
        PRINT_LINK config directive parser. 
        Installs a lookup method to search a page for 'print page',
        'print this article', etc. links
        """

        m = re.search(r'''^["'](.+)['"]$''', data)
        if not m:
            raise AutoDiscoveryError, "Invalid data passed to 'PRINT_LINK' config command"

        link_text = m.group(1).lower()

        def make_sense(tag):
            """
            A sense maker function. Makes sense out of a tag.
            In a sense that a href could be whacky 'javascript:...' which
            we need to decipher.
            """

            def js_find(js):
                """ Try to make sense of a javascript link """
                # Examples:
                #  javascript:printopen('/print/society/anomal/104620-disappear-0');
                #  javascript:PopUp('you_popup','/pages/text/print.html?in_article_id=541334&in_page_id=1965','500','500','1','yes')

                m = re.search(r'''(["'])(?P<href>/.+?)\1''', js)
                if m:
                    return m.group('href').replace('&amp;', '&')

                return None
            
            ok_starts_with = ['http://', '/', '../', './', '?']
            try:
                for ok in ok_starts_with:
                    if tag['href'].startswith(ok):
                        return tag['href'].replace('&amp;', '&')
            except KeyError:
                # there is no 'href' attribute for this tag
                return None

            # 'href' attribute is something else than a normal link,
            # possibly javascript:
            return js_find(tag['href'])

        def mk_print_link_lookup():
            def print_link_lookup(tag):
                """ Look for an 'a' tag with link_text """
                if tag.name != 'a':
                    return False

                for sibling in tag:
                    try:
                        text = sibling.string.strip().lower()
                        if text == link_text:
                            return True
                    except AttributeError:
                        try:
                            # some sites have print icons with the same alt
                            # text as we are looking for in <a>
                            for text in (sibling['alt'].strip().lower(),
                                sibling['title'].strip().lower()
                            ):
                                if text == link_text:
                                    return True
                        except KeyError:
                            continue
                return False
            print_link_lookup.make_sense = make_sense
            return print_link_lookup
       
        # this is not nice, we are adding the same function for each string
        # TODO: add one function which loops over all strings, rather than
        # a function for each sting
        self.lookups.append(mk_print_link_lookup())

    def _rewrite_url(self, data):
        """
        REWRITE_URL config directive parser. 
        Installs an URL rewriter.
        """
        
        try:
            host_re, from_re, to_re = re.split(r'\s+|\t+', data)
        except ValueError:
            raise AutoDiscoveryError, "Invalid data passed to REWRITE_URL config command"

        def mk_rewriter():
            def should_rewrite(url):
                parsed = urlparse.urlparse(url)
                if re.search(host_re, parsed[1]): # 1 is host
                    return True
                return False
            def rewrite(url):
                url = re.sub(from_re, to_re, url)
                return url
            should_rewrite.rewrite = rewrite
            return should_rewrite

        self.rewriters.append(mk_rewriter())

    def _ignore_url(self, data):
        """
        IGNORE_URL config directive parser.
        Installs ignore list.
        """

        def ignore(url):
            if re.search(data, url):
                return True

        self.ignores.append(ignore)
    
    def autodiscover(self, url):
        """
        Given a url, autodiscover mobile version of the url
        Returns the mobile URL, or None, if none was discovered.
        """

        # Test if the url should not be ignored
        #
        for ign in self.ignores:
            if ign(url):
                return None

        # Call the url rewriters, as they do not require
        # to fetch the content of a page.
        #
        for rw in self.rewriters: # rw is a function
            if rw(url):
                url = rw.rewrite(url)
                return url

        content = self._get_page(url)
        soup = BeautifulSoup(content)

        # Lets see if the page has a
        # <link rel="alternate" media="handheld" href="..."> tag
        #
        def link_finder(tag):
            if tag.name == 'link' and tag.has_key('media') and 'handheld' in tag['media']:
                return True
            return False

        link = soup.find(link_finder)
        if link and link.has_key('href'):
            return link['href']

        for lookup in self.lookups: # lookup is a function
            tag = soup.find(lookup)
            if tag:
                if hasattr(lookup, 'make_sense'):
                    # A lookup function can have a 'make_sense' attribute
                    # which is a function makes "make sense" out of a
                    # tag. A href could be javascript link, we might need to
                    # do a little more extraction.
                    href = lookup.make_sense(tag)
                    if not href:
                        return None
                else:
                    href = tag['href']
            
                return urlparse.urljoin(url, href)
        
        return None

    def _get_page(self, url):
        """ Gets and returns a web page at url """
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')

        try:
            content = urllib2.urlopen(request)
            return content.read()
        except (urllib2.HTTPError, urllib2.URLError, socket.error, socket.sslerror), e:
            raise AutoDiscoveryError, e


if __name__ == "__main__":
    try:
        prog, url = sys.argv
    except ValueError:
        print "Usage: " + sys.argv[0] + ' <URL>'
        sys.exit(1)

    ad = AutoDiscovery();
    mobile_url = ad.autodiscover(url)

    if not mobile_url:
        print "No mobile url was found for '%s'!" % url
        sys.exit(1)

    print mobile_url

