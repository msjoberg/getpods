#!/usr/bin/env python

from __future__ import print_function

# http://wiki.python.org/moin/RssLibraries
import feedparser
from pprint import pprint

debug = True

#------------------------------------------------------------------------------

class Item(object):
    """
    Class encapsulating the information for a single podcast item,
    i.e. a single episode.  Also contains a static cache keeping track
    of already downloaded episodes.
    """

    cache = {}
    cache_read = False

    def __init__(self, item_data):
        if not Item.cache_read:
            Item.read_cache()

        self.data = item_data

    def is_new(self):
        return self.guid() not in Item.cache

    def mark_as_seen(self):
        Item.cache[self.guid()] = 1

    def guid(self):
        """Method that determines and return a unique identifier of
        the item."""

        return self.data["guid"]

            # print(item["guid"])
            # for media in item["media_content"]:
            #     print(" *", media["url"])

    @staticmethod
    def save_cache():
        """Saves cache from memory to file."""

        with open("cache", "w") as fp:
            for guid in Item.cache:
               fp.write(guid+"\n")

    @staticmethod
    def read_cache():
        """Reads old cache from file to memory."""

        try:
            with open("cache") as fp:
                for line in fp:
                    Item.cache[line.rstrip()] = 1
        except:
            pass
        Item.cache_read = True

#------------------------------------------------------------------------------

class Feed(object):
    """
    Class encapsulating the information for a podcast feed.
    """

    def __init__(self, url, dirname):
        self.url = url
        self.dirname = dirname

        if debug:
            print("Feed:", dirname, "["+url+"]")

    def update(self):
        feed_data = feedparser.parse(self.url)

        feed_title = feed_data["channel"]["title"]
        print(" * Updating", feed_title)

        for item_data in feed_data["items"]:
            item = Item(item_data)
            if item.is_new():
                print(item.guid())
            item.mark_as_seen()

        Item.save_cache()


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

def main():
    feed_list = read_urls("urls-test")

    for feed in feed_list:
        feed.update()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
