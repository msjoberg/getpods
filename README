getpods.py is a very simple command line podcast client in Python, 
that I made for my personal use.

# Usage, configuration

You need a directory for your podcasts, e.g. `~/Podcasts` or directly
on your mounted media player (like I have). You should make a
configuration called `~/.getpods` that points to this directory. There
should be a file getpods.sample.conf distributed together with this
script that you can copy to `~/.getpods` and modify.

In the podcast_dir directory, create a file called `urls` which
contains one line for each podcast feed with the following format:

    # comments preceeded by hash
    url directory_name [?]

For example:

    # These are my awesome podcast feeds
    http://faif.us/feeds/cast-ogg/ faif
    http://hackerpublicradio.org/hpr_ogg_rss.php hpr ?

The question mark is for feeds where the program should query about
each new episode.  Other feeds have new episodes automatically
downloaded.


# Implementation 

It's a simple Python script, that requires the feedparser and pycurl
modules.  In Debian this should mean installing the packages
`python-feedparse` and `python-pycurl`.

Episodes that have been downloaded or otherwise marked as "seen" are
registered in a file called "cache" in the podcast_dir.
