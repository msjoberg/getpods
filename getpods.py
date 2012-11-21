#!/usr/bin/env python

from __future__ import print_function

# http://wiki.python.org/moin/RssLibraries
import feedparser
from pprint import pprint

debug = True

#------------------------------------------------------------------------------

class Feed(object):
    """Class encapsulating the information for a podcast feed."""

    def __init__(self, url, dirname):
        self.url = url
        self.dirname = dirname

        if debug:
            print("Feed:", dirname, "["+url+"]")

#------------------------------------------------------------------------------

def read_urls(urls_fname):
    """
    Function to read the "urls" file which contains one line for each
    podcast feed with the following format:

    # comments preceeded by hash
    url directory_name

    For example:
    http://faif.us/feeds/cast-ogg/ faif
    """
    feed_list = []
    
    with open(urls_fname) as fp:
        for line in fp:
            if line[0] == '#':
                continue
            parts = line.rstrip().split()
            feed_list.append(Feed(parts[0], parts[1]))

    return feed_list

#------------------------------------------------------------------------------

def update_feed(feed_url):
    feed = feedparser.parse(feed_url)

    feed_title = feed["channel"]["title"]
    print(feed_title)

    for item in feed["items"]:
        print(item["guid"])
        for media in item["media_content"]:
            print(" *", media["url"])
#    pprint(item)

#------------------------------------------------------------------------------

# $ ./getpods.py
# for each feed:
#   update_feed
#   for each new item in feed:
#     add to list of new items

def main():
    feed_list = read_urls("urls-test")

    for feed in feed_list:
        update_feed(feed.url)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
