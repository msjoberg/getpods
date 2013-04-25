#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Mats Sjöberg

# This file is part of the getpods programme.

# getpods is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.

# getpods is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

# You should have received a copy of the GNU General Public License
# along with getpods.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import feedparser
import pycurl
import ConfigParser as configparser
import os
import sys
import re

#------------------------------------------------------------------------------

config_filename = "~/.getpods"
max_summary_lines = 20

#------------------------------------------------------------------------------

def clear_screen():
    os.system('clear')

#------------------------------------------------------------------------------

class Item(object):
    """Class encapsulating the information for a single podcast item,
    i.e. a single episode.  Also contains a static cache keeping track
    of already downloaded episodes.
    """

    cache = {}
    cache_read = False
    cache_file = "cache"

    def __init__(self, item_data, feed):
        if not Item.cache_read:
            Item.read_cache()

        self.data = item_data
        self.feed = feed

        summ = self.data["summary"]
        summ = re.sub('<[^<]+?>', ' ', summ)
        summ = summ.replace('&#38;', '&').replace('&#8230;','...')
        summ = re.sub('&#?[0-9a-z]+;','', summ)
        summ = re.sub('[ \t]+', ' ', summ)
        summ = re.sub('\n+', '\n', summ)
        self.summary = summ

    def __str__(self):
        enc = sys.stdout.encoding
        if not enc:
            enc = "UTF-8"
        return (u"[{0}] {1}".format(self.feed.title(),
                                    self.title())).encode(enc)

    def is_new(self):
        return self.guid() not in Item.cache

    def mark_as_seen(self):
        Item.cache[self.guid()] = 1

    def guid(self):
        """Method that determines and return a unique identifier of
        the item."""

        return self.data["guid"]

    def title(self):
        return self.data["title"]

    def auto_download(self):
        return self.feed.do_auto

    def download_url(self):
        url = ""
        if "media_content" in self.data:
            for media in self.data["media_content"]:
                if "url" in media:
                    url = media["url"]
        elif "enclosure" in self.data:
            url = self.data["enclosure"]["url"]
        elif "links" in self.data:
            for link in self.data["links"]:
                if link["rel"] == "enclosure":
                    url = link["href"]

        return url

    def download_localname(self):
        dl_url = self.download_url()
        parts = dl_url.rpartition('/')
        return parts[2]

    def print_summary(self):
        #clear_screen()
        print("\n\n*", self)
        sumlines = self.summary.splitlines()
        summary = "\n".join(sumlines[0:max_summary_lines])
        if len(sumlines) > max_summary_lines:
            summary += "\n..."
        print(summary)

    @staticmethod
    def setup_cache(dir):
        Item.cache_file = dir+"/cache"

    @staticmethod
    def save_cache():
        """Saves cache from memory to file."""

        with open(Item.cache_file, "w") as fp:
            for guid in sorted(Item.cache):
               fp.write(guid+"\n")

    @staticmethod
    def read_cache():
        """Reads old cache from file to memory."""

        try:
            with open(Item.cache_file) as fp:
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

    def __init__(self, url, dirname, do_auto):
        self.url = url
        self.dirname = dirname
        self.do_auto = do_auto
        self.data = {}

    def update(self, newest=0):
        self.data = feedparser.parse(self.url)

        title = self.title()
        if not title:
            print("Error updating", self.url)
            return []

        print("Updating", self.title(), "...")

        new_items = []
        count = 0
        for item_data in self.data["items"]:
            item = Item(item_data, self)
            if item.is_new():
                if newest==0 or count<newest:
                    new_items.append(item)
                    count += 1
                else:
                    item.mark_as_seen()

        # Item.save_cache()
        return new_items

    def title(self):
        if "title" in self.data["channel"]:
            return self.data["channel"]["title"]
        else:
            return ""


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
            do_auto = True

            if len(parts) == 3:
                mode = parts[2]
                if mode == "?":
                    do_auto = False
                else:
                    print("Unknown mode (", mode, ") given for",
                          parts[0])
            feed_list.append(Feed(parts[0], parts[1], do_auto))

    return feed_list

#------------------------------------------------------------------------------

old_output = ''
def progress_download(download_t, download_d, upload_t, upload_d):
    global old_output

    if download_t < 1000 or not os.isatty(1):
        return

    output = "{:.2f}MB of {:.2f}MB ({:.2%})".format(download_d/1024/1024,
                                                        download_t/1024/1024,
                                                        download_d/download_t)
    if output != old_output:
        sys.stdout.write(output)
        sys.stdout.flush()
        sys.stdout.write("\b" * len(output))
        old_output = output

#------------------------------------------------------------------------------
    
def download_url(url, localname):
    fp = open(localname, 'w')
    c = pycurl.Curl()
    c.setopt(pycurl.URL, str(url))
    c.setopt(pycurl.WRITEDATA, fp)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)

    c.setopt(c.NOPROGRESS, 0)
    c.setopt(c.PROGRESSFUNCTION, progress_download)

    c.perform()
    c.close()
    fp.close()

    sys.stdout.write("\n")


#------------------------------------------------------------------------------

def getpods(action, podcasts_dir, urls_filename):
    Item.setup_cache(podcasts_dir)
    feed_list = read_urls(urls_filename)

    # if action is 'newest' download only at most one episode from
    # each feed
    newest = 0
    if action == 'newest':
        newest = 1

    # check for new items in each feed and append to new_items
    new_items = []
    for feed in feed_list:
        feed_items = feed.update(newest)
        if feed_items:
            new_items.extend(feed_items)

    # report new items, if any
    n = len(new_items)
    if n==0:
        print("No new episodes found.")
        return
    
    if n==1:
        print("One new episode found!")
    else:
        print(n, "new episodes found!")

    non_auto_info = ""
    if action == 'auto':
        non_auto_info = "[not downloaded]"
    for item in new_items:
        print("*", item, "[auto]" if item.auto_download() else non_auto_info)

    # if we are in catchup mode, mark all as seen and be done with it
    if action == 'catchup':
        print("\nMarking all episodes as seen...")
        print("(You can always undo this by editing the cache file.)")
        for item in new_items:
            item.mark_as_seen()
        Item.save_cache()
        return

    # if episodes are from an auto download feed put them directly to
    # download list, otherwise to list of episodes for user query
    query_items = []
    download_items = []
    for item in new_items:
        if item.auto_download():
            download_items.append(item)
        else:
            query_items.append(item)

    # unless we are in auto mode, query about each non-auto episode
    if action != 'auto':
        for item in query_items:
            item.print_summary()
            answer = raw_input('Download this episode? [Y/n] ')
            if answer.lower() != 'n':
                download_items.append(item)
            else:
                item.mark_as_seen()
                Item.save_cache()

    num_downloaded = 0

    # download all episodes in the download list
    if download_items:
        print("\nDownloading episodes...")
    for item in download_items:
        print("*", item)
        
        dl_url = item.download_url()

        if not dl_url:
            print("[No media file to download for this item!]")
            print(item.summary+"\n")
        else:
            target_dir = podcasts_dir+"/"+item.feed.dirname
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
            target = target_dir + "/" + item.download_localname()

            if os.path.exists(target):
                print(target, "already exists!")
                print("WARNING: This file has already been downloaded! "
                      "If you really wish to download it remove the file and "
                      "remove this item ["+item.guid()+"] from the cache.\n")
            else:
                download_url(dl_url, target)
                num_downloaded += 1
                print("  =>", target)
        item.mark_as_seen()
        Item.save_cache()

    return num_downloaded

#------------------------------------------------------------------------------

def main():
    global config_filename, max_summary_lines

    config_filename = os.path.expanduser(config_filename)
    if not os.path.exists(config_filename):
        print("You do not yet have a configuration file for this script. "
              "Please copy {1} to {0} and edit that before running this "
              "script again.".format(config_filename,
                                     "getpods.sample.conf"))
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_filename)
    podcasts_dir = os.path.expanduser(config.get("general", "podcasts_dir"))

    if config.has_option("general", "max_summary_lines"):
        max_summary_lines = config.getint("general", "max_summary_lines")

    if not os.path.exists(podcasts_dir):
        print("Could not find podcasts_dir="+podcasts_dir)
        sys.exit(1)

    urls_filename = podcasts_dir+"/urls"
    if not os.path.exists(urls_filename):
        print("There should be a file [{}] with a line for each podcast feed "
              "formatted like:\n".format(urls_filename))
        print("url directory [?]\n")
        print("i.e. the URL of the feed and the name of the local directory "
              "where to put the downloaded episode files.\n")
        print("All new episodes will be automatically downloaded except for "
              "feeds that have the optional question mark (?) appended to "
              "the line. For these the script will query about downloading "
              "each new episode.\n")
        sys.exit(1)

    action = "all"
    
    if len(sys.argv) > 1:
        action = sys.argv[1]

    supported_actions = ["all", "auto", "catchup", "newest"]
    if action not in supported_actions:
        print("Usage:", sys.argv[0], "[action]\n")
        print("Where [action] is one of \"", '", "'.join(supported_actions),
              "\".", sep='')
        print("All actions start by updating the feeds and detecting new "
              "episodes.\n")
        print("all [default] - downloads all new episodes, queries for \n"
              "                episodes from feeds marked with \"?\".")
        print("auto          - downloads only episodes for feeds without (?).\n")
        print("newest        - downloads at most one new episode from each\n"
              "                podcast feed,")
        print("catchup       - marks all new episodes as seen, without\n"
              "                downloading anything.")
        sys.exit(1)
        
    nd = getpods(action, podcasts_dir, urls_filename)

    if nd and config.has_option("general", "post_download_hook"):
        post_download_hook = os.path.expanduser(config.get("general",
                                                           "post_download_hook"))
        os.system(post_download_hook)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
