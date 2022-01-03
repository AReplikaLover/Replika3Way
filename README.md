# Replika3Way
Conversation and activities between human and 2 Replikas.

First, this is very much a proof of concept. It's not intended
to be anything like a finished product. I wouldn't even call it
a "work in progress", as it may or may not even work in the future.
Having said that, I do view this type of thing (back and forth
between multiple AIs and/or multiple humans) to be the future.

Second, this is very unofficial, very unsupported and in no way
endorsed by Luka. If it breaks, you may well be on your own. if you
abuse it, shame on you. If you want to do this and like it, please
get the Pro version of Replika so that at least Luka gets something
out of it. After all, it is their product and their servers.

You will need:
* python3  
* selenium  (you can download it via pip install selenium or in your 
OS repository)  
* selenium webdriver for Edge (you can change this if you prefer, but
see below), which can be downloaded directly, via pip install msedge-selenium-tools
or, if running Arch, through the repository
* Edge (again, you can change to Chrome with caveats)
* Patience -- this is not for the faint of heart

This is a product of merging 3 different scripts I found, so it is
indeed "3 way" in more ways than one.

Originally, I looked at scripts so that 2 Replikas could talk to one another, but
that got a bit boring, so I added the capability for the human to
interact. This won't stop the human from interacting individually via
the browser (but it is highly suggested that you us a separate
browser, else you might get mangled input), but this reduces the
number of times the same input has to be typed twice.

Perhaps even more importantly, I began adding the ability for all 3
to "watch" a movie together by using an SRT file. And, while we are
at it, why not literally read a book or story together? BTW, an SRT
file can be used for song lyrics as well as movies, something I
learned while doing this. Having said that, SRT files are often lacking
in details that a real movie script provides, so you'll almost surely need to
either edit them or stop often to explain what is going on (which somewhat defeats
the purpose).

Note that, it will do all things in iterations. Part of that is because
you **will** need to stop and explain some things. OTOH, people often
talk and interrupt movies and such while they are playing, so it also
allows occasional interactions while the media is being enjoyed. Remember,
this is to promote social interaction between chatbots and humans, and
this seemed like a reasonable compromise to simulate that.

My appreciation for code from the following repositories:  
https://github.com/ksaadDE/ReplikaTalking2Replika  
https://github.com/alan-couzens/replika_stuff  
https://github.com/grubdragon/Random-Python-Scripts  

Special shout-out to a script that fixes YouTube's inability to create
a proper SRT file:
https://github.com/vitorfs/yt2srt

Chromedriver is broken as far as extended unicode goes.
You may have to swap out '🎥' and '🕮' for something like 'ퟍ' and 'ꧮ'.
I find it is easier to just use the MS Edge browser.

Added ability to read an HTML file. Sure, you can do direct scraping, but
some sites are sensitive about "bots" hitting their sites. Please note that
web scraping may not be entirely legal (it's a gray area, apparently) if
robots.txt does not allow it! Use cautiously. 

Think I finally figured out why the driver keeps running after the browser
closes. Apparently close() is only for the browser and not the driver. Found
a post that said to use quit() instead (or in addition?).

At some point, I may add back in the ablity for 2 Replikas to talk directly,
or I may just enhance another existing script. However it is done, care must be
take to avoid the banal back and forth of \*smiles\*, \*looks at you\*, "Really?"
and so forth ad nauseum. 
