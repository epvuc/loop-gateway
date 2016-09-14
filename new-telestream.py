#! /usr/bin/python
#
# 
# This program signs into Twitter using the twitter streaming API and 
# subscribes to a specified search pattern, feeding matching tweets to
# the teletype loop via TCP connection to the ser.py process as they
# are received in realtime from Twitter. 
# It makes an attempt to avoid backlogs for searches that produce a lot
# of output by selectively dropping tweets as the backlog builds. 
# It assumes a 60wpm loop and will try to avoid more than a couple of
# minutes printing backlog. 
# 
# To use this, you will need to register it with twitter as an application
# and get an oauth consumer key and consumer secret,  then authorize the
# application to your preferred twitter account and get an access token 
# and access token secret, which should be filled in below. 


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import simplejson as json
import time
import HTMLParser
import unicodedata
import re
import sys
import textwrap
import socket
from datetime import datetime
from dateutil import tz,parser

skip_retweets = False
myscreenname = 'MY_TWITTER_USERNAME'

# halfassed attempt to match "any" url, since we don't want to print them
# see http://daringfireball.net/2010/07/improved_regex_for_matching_urls
GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')

# oauth consumer and access tokens, these have to be done manually
consumer_key="YOUR_TWITTER_CONSUMER_KEY"
consumer_secret="YOUR_TWITTER_CONSUMER_SECRET"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="YOUR_ACCESS_TOKEN"
access_token_secret="YOUR_ACCESS_TOKEN_SECRET"

LTRS = ( 'E', 'A', 'S', 'I', 'U', 'D', 'R', 'J', 'N', 'F', 'C', 'K', 
         'T', 'Z', 'L', 'W', 'H', 'Y', 'P', 'Q', 'O', 'B', 'G', 'M', 'X', 'V')

FIGS = ( '3', '-', '8', '7', '$', '4', '\'', ',', '!', ':', '(', '5', 
         '"', ')', '2', '#', '6', '0', '1', '9', '?', '&', '.', '/', ';')


class Teletype:
    """ teletype interface, try to turn tweets into something
    printable on a teletype machine"""

    def __init__(self, hmhost):
        self.hparser = HTMLParser.HTMLParser()
        self.edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
                       ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!') ]
        self.baudrate = 45.45
        # initialize backlog management data
        self.last_sent = 0
        self.expected_done = 0
        self.backlog = 0
	self.max_backlog = 6
        # establish a connection to the teletype machine.
        self.ttysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ttysock.connect(hmhost)
        print "connected."

    def sendtime(self, text):
        ccount = 0
        curcase = 'ltrs'
        prevcase = 'ltrs'
        for c in text:
            if c.upper() in FIGS:
                curcase = 'figs'
            elif c.upper() in LTRS:
                curcase = 'ltrs'
            ccount = ccount + 1
            if curcase != prevcase:
                ccount = ccount+1
            prevcase = curcase
        return (7.42/self.baudrate)*ccount

    def debugprint(self, text):
        foo = text.replace('\n', '[LF]\n')
        foo = foo.replace('\r', '[CR]\r')
        print foo

    def output(self, blob):
        # bail out of processing this tweet if any of the necessary fields are missing

        try:
            tweet=json.loads(blob)
        #    print tweet
            if 'direct_message' in tweet:
                msgtype = 'dm'
                screenname = self.hparser.unescape(tweet['direct_message']['sender_screen_name'])
                screenname = unicodedata.normalize('NFKD', unicode(screenname)).encode('ascii', 'ignore')
                if screenname == myscreenname:
                    return
                text = self.hparser.unescape(tweet['direct_message']['text'])
                text = unicodedata.normalize('NFKD', unicode(text)).encode('ascii', 'ignore')
                pdate_utc = parser.parse(tweet['direct_message']['created_at'])
            else:
                msgtype = 'tweet'
                screenname = self.hparser.unescape(tweet['user']['screen_name'])
                screenname = unicodedata.normalize('NFKD', unicode(screenname)).encode('ascii', 'ignore')
                author = self.hparser.unescape(tweet['user']['name'])
                author = unicodedata.normalize('NFKD', unicode(author)).encode('ascii', 'ignore')
                text = self.hparser.unescape(tweet['text'])
                text = unicodedata.normalize('NFKD', unicode(text)).encode('ascii', 'ignore')
                # get the posting date as a short format in local timezone
                pdate_utc = parser.parse(tweet['created_at'])
        except:
            # raise
            return

        # don't print retweets.
        if "retweeted_status" in tweet:
            if skip_retweets:
                return
        utc = pdate_utc.replace(tzinfo=tz.tzutc())
        pdate_local = utc.astimezone(tz.gettz('America/Los_Angeles'))
        pdate_localshort = datetime.strftime(pdate_local, "%H:%M %a")

        # strip out anything that looks like a URL
        text = re.sub(GRUBER_URLINTEXT_PAT, "URL", text)
        # construct the whole block to be printed
        if msgtype == 'dm':
            block = '--' + chr(7)+' '+chr(7)+'DM from ' + screenname+', ' + pdate_localshort + ': ' + text + '\n'
        else:
            block = author + ' ('+screenname+'), ' + pdate_localshort + ': ' + text + '\n'

        for (orig, repl) in self.edits:
            block = block.replace(orig, repl)
        indent = 4
        # justify/format only after all edits are made.
        fmtblock = '\n'.join(textwrap.wrap(block, width=66, 
                             initial_indent='', subsequent_indent=' '*indent))

        # hand it off to the heavymetal process

        # if the last time we sent a message to the tty was long enough ago
        # that we have probably finished printing everything in the backlog,
        # reset the backlog.
        if (self.backlog > 0) and (time.time() > self.expected_done): 
            self.backlog = 0

        # if we're going to queue this message for printing
        if self.backlog < self.max_backlog: 
            # if this is the first message since the backlog cleared
            if self.backlog == 0:
                self.last_sent = time.time()
                self.expected_done = self.last_sent + self.sendtime(fmtblock)
                
            self.ttysock.sendall(fmtblock.upper() + '\n \n')
            print '*** Printing, now', time.time(), 'lastsent', (time.time()-self.last_sent), 'secs ago, expected_done', self.expected_done-time.time(), 'secs from now, backlog', self.backlog
            self.debugprint(fmtblock)
            # add length of this message to the remaining backlog, and increment the backlog count
            self.expected_done = self.expected_done - (time.time()-self.last_sent) + self.sendtime(fmtblock)
            self.last_sent = time.time()
            self.backlog = self.backlog + 1
        else:
            # we've reached max backlog, start dropping messages
            print '--- Dropped, now', time.time(), 'lastsent', (time.time()-self.last_sent), 'secs ago, expected_done', self.expected_done-time.time(), 'secs from now, backlog', self.backlog
            self.debugprint(fmtblock)

class StdOutListener(StreamListener):
    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    def on_data(self, data):
        tty.output(data)
        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    tty = Teletype(hmhost=('localhost', 11123))
    stream = Stream(auth, l)
    # with args, use args as search terms
    if len(sys.argv) > 1:
        tty.ttysock.sendall('streaming search terms.\n\n')
        stream.filter(track=sys.argv[1:])
    else: 
	# stream our own twitter timeline
        tty.ttysock.sendall('streaming timeline.\n\n')
        stream.userstream(myscreenname)

