#! /usr/bin/python
# Show recent twitter updates to an account. Intended for use as a plugin 
# for printing on a teletype - the output will be correctly processed and formatted 
# for the limited teletype character set and line width. 
# - eric volpe 12/2014

# It will need write access to /var/lib/last_twitterid in order to keep track of
# what it's already shown. 

# If you are not in the US Pacific timezone, replace all references to 
# "America/Los_Angeles" with the appropriate named timezone from here:
# http://en.wikipedia.org/wiki/List_of_tz_database_time_zones

# it requires the "tweepy" python library for talking to twitter among some
# others below:

# You will need to register it as an app with twitter to get a consumer token and key,
# and then authorize the app to access your own twitter account to get an access
# token and access token secret. 

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

# oauth consumer and access tokens that identify the app itself to twitter's API
consumer_key="MY_TWITTER_CONSUMER_KEY"
consumer_secret="MY_TWITTER_CONSUMER_SECRET"

def store_last(lastblob):
    try:
        with open('/var/lib/last_twitterid', 'w') as f: f.write(json.dumps(lastblob)+'\n')
    except:
        print "failed to store last twitterid to /var/lib/last_twitterid"
        return

def fetch_last():
    try:
        with open('/var/lib/last_twitterid', 'r') as f:
            lastblob = json.loads(f.read())
    except:
        lastblob = {}
        lastblob['last_twitterid'] = 1
        lastblob['last_dm'] = 1
        lastblob['last_mention'] = 1
        lastblob['access_token'] = 'MY_TWITTER_ACCESS_TOKEN'
        lastblob['access_token_secret'] = 'MY_TWITTER_ACCESS_TOKEN_SECRET'

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
        numtweets = 10
    else:
        numtweets = int(sys.argv[1])

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)

    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print 'Error! Failed to get request token for this app.'
	sys.exit()

    # fetch saved OAuth token if we have it.
    lasts = fetch_last()
    if 'access_token' in lasts:
        access_token = lasts['access_token']
    else:
        access_token = ''
    if 'access_token_secret' in lasts:
        access_token_secret = lasts['access_token_secret']
    else:
        access_token_secret = ''

    auth.set_access_token(access_token, access_token_secret)
    api=tweepy.API(auth)
    try:
        ratelimit=api.rate_limit_status()
    except:
        print "Visit the following URL while logged into twitter,"
        print "Then copy the resulting token back here."
        print "redirect_url is", redirect_url
        verifier = raw_input('Verifier:')

        try:
            auth.get_access_token(verifier)
            api=tweepy.API(auth)
            ratelimit=api.rate_limit_status()
        except tweepy.TweepError:
            print 'Error! Failed to get access token.'
            sys.exit()

    try:
        api = tweepy.API(auth)
    except:
        print "OAuth transaction did not work."
        sys.exit()

    # save the good access token/key we have established, for next time
    access_token = auth.access_token.key
    access_token_secret = auth.access_token.secret
    lasts['access_token'] = access_token
    lasts['access_token_secret'] = access_token_secret
    # we haven't fetched anything yet so the saved timeline pointers are still valid.
    store_last(lasts)   

    if int(ratelimit['resources']['statuses']['/statuses/home_timeline']['remaining']) < 1:
        print "twitter API rate limit exceeded."
        sys.exit()

    lasts = fetch_last()
    print "ZCZC TWITTER UPDATES"   

    # print our "Timeline"
    results = tweepy.Cursor(api.home_timeline, lasts['last_twitterid']).items(numtweets)
    ids_printed = print_statuses(results, '')
    if len(ids_printed) > 0:
        lasts['last_twitterid'] = max(ids_printed)
    else:
        print "no new tweets."

    # Print recent mentions of us.
    results = tweepy.Cursor(api.mentions_timeline, lasts['last_mention']).items(numtweets)
    ids_printed = print_statuses(results, "New Mentions:")
    if len(ids_printed) > 0:
        lasts['last_mention'] = max(ids_printed)
    else:
        print "no new mentions."

    # Print direct messages to us.
    results = tweepy.Cursor(api.direct_messages, lasts['last_dm']).items(numtweets)
    ids_printed = print_directmessages(results, "New Direct Messages:")
    if len(ids_printed) > 0:
        lasts['last_dm'] = max(ids_printed)
    else:
        print "no new direct messages."

    store_last(lasts)
    print "NNNN"


