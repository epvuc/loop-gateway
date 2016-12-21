#! /usr/bin/python
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import tweepy
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

skip_retweets = True

# halfassed attempt to match "any" url, since we don't want to print them
# see http://daringfireball.net/2010/07/improved_regex_for_matching_urls
GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')

edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
          ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!') ]

# oauth consumer and access tokens, these have to be done manually
consumer_key="YOUR_TWITTER_CONSUMER_KEY"
consumer_secret="YOUR_TWITTER_CONSUMER_SECRET"


# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="YOUR_ACCESS_TOKEN"
access_token_secret="YOUR_ACCESS_TOKEN_SECRET"

def store_last(lastblob):
    try:
        with open('/tmp/last_twitterid', 'w') as f: f.write(json.dumps(lastblob)+'\n')
    except:
        #print "failed to store last twitterid to /tmp/last_twitterid"
        return

def fetch_last():
    try:
        with open('/tmp/last_twitterid', 'r') as f:
            lastblob = json.loads(f.read())
    except:
        lastblob = {}
        lastblob['last_twitterid'] = 1
        lastblob['last_dm'] = 1
        lastblob['last_mention'] = 1

    return lastblob

def print_statuses(results, header):
    hparser = HTMLParser.HTMLParser()
    count=0
    ids_printed = []

    for result in results:
        if hasattr(result, "retweeted_status"):
            if skip_retweets:
                continue
        count = count + 1
        if count > 100:
            continue
        if header and count == 1:
            print header

        screenname = hparser.unescape(result.user.screen_name)
        screenname = unicodedata.normalize('NFKD', unicode(screenname)).encode('ascii', 'ignore')
        author = hparser.unescape(result.user.name)
        author = unicodedata.normalize('NFKD', unicode(author)).encode('ascii', 'ignore')
        text = hparser.unescape(result.text)
        text = unicodedata.normalize('NFKD', unicode(text)).encode('ascii', 'ignore')
        pdate_utc = parser.parse(unicode(result.created_at))
        utc = pdate_utc.replace(tzinfo=tz.tzutc())
        pdate_local = utc.astimezone(tz.gettz('America/Los_Angeles'))
        day=pdate_local.day
        month=pdate_local.month
        year=pdate_local.year
        time=datetime.strftime(pdate_local, "%H:%M %a")
        pdate_localshort = '%s %d/%d/%d' % (time, month, day, year)

        # strip out anything that looks like a URL
        text = re.sub(GRUBER_URLINTEXT_PAT, "URL", text)
        # construct the whole block to be printed
        #block = str(count)+') '+ author + ' ('+screenname+'), ' + pdate_localshort + ': ' + text + '\n'
        block = author + ' ('+screenname+'), ' + pdate_localshort + ': ' + text + '\n'

        for (orig, repl) in edits:
            block = block.replace(orig, repl)
        indent = 4
        # justify/format only after all edits are made.
        fmtblock = '\n'.join(textwrap.wrap(block, width=66, 
                             initial_indent='', subsequent_indent=' '*indent))
        print fmtblock
        print ""
        ids_printed.append(result.id)

    return(ids_printed)

def print_directmessages(results, header):
    hparser = HTMLParser.HTMLParser()
    count=0
    ids_printed = []

    for result in results:
        count = count + 1
        if count > 100:
            continue
        if header and count == 1:
            print header

        screenname = hparser.unescape(result.sender.screen_name)
        screenname = unicodedata.normalize('NFKD', unicode(screenname)).encode('ascii', 'ignore')
        author = hparser.unescape(result.sender.name)
        author = unicodedata.normalize('NFKD', unicode(author)).encode('ascii', 'ignore')
        text = hparser.unescape(result.text)
        text = unicodedata.normalize('NFKD', unicode(text)).encode('ascii', 'ignore')
        pdate_utc = parser.parse(unicode(result.created_at))
        utc = pdate_utc.replace(tzinfo=tz.tzutc())
        pdate_local = utc.astimezone(tz.gettz('America/Los_Angeles'))
        day=pdate_local.day
        month=pdate_local.month
        year=pdate_local.year
        time=datetime.strftime(pdate_local, "%H:%M %a")
        pdate_localshort = '%s %d/%d/%d' % (time, month, day, year)

        # strip out anything that looks like a URL
        text = re.sub(GRUBER_URLINTEXT_PAT, "URL", text)
        # construct the whole block to be printed
        #block = str(count)+') '+ author + ' ('+screenname+'), ' + pdate_localshort + ': ' + text + '\n'
        block = author + ' ('+screenname+'), ' + pdate_localshort + ': ' + text + '\n'

        for (orig, repl) in edits:
            block = block.replace(orig, repl)
        indent = 4
        # justify/format only after all edits are made.
        fmtblock = '\n'.join(textwrap.wrap(block, width=66, 
                             initial_indent='', subsequent_indent=' '*indent))
        print fmtblock
        print ""
        ids_printed.append(result.id)

    return(ids_printed)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: tsearch searchterms"
        sys.exit()

    # numtweets = int(sys.argv[1])
    numtweets = 10
    search = sys.argv[1:]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api=tweepy.API(auth)

    # do search and print results
    results = tweepy.Cursor(api.search, q=search, result_type="recent").items(numtweets)
    ids_printed = print_statuses(results, 'search results:')
    if len(ids_printed) == 0:
        print "no results."



