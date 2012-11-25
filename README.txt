* Usage, configuration

First create a file called "urls" which contains one line for each
podcast feed with the following format:

    # comments preceeded by hash
    url directory_name

    For example:
    http://faif.us/feeds/cast-ogg/ faif

[Q] Maybe have a setting for always download or always ask for each podcast?

    ./getpods.py update

Should update all feeds and make a list of new episodes. Those that
should be asked about are presented interactively at the end.

Updating Free as in Freedom ...
Updating Linux Outlaws ...

New episodes found:
- 

* Implementation.

cache file, one line for each unique item guid/id
read in store as hash

fetch feeds, compare with hash, if new add url to list of new eps

ask about some eps, if answer is no remove and place in cache list

download all in new list, place in cache after successful dl
