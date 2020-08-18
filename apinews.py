#! /usr/bin/python

# This uses http://newsapi.org 's API to get recent news headlines.
# It will need the python dateutil module (pip install dateutil) 
# and the newsapi.org python module (pip install newsapi-python)
# Also, you'll need to sign up for a free individual account at
# newsapi.org and get an API key, which you should then enter here
# replacing the text "MY_API_KEY"
# eric volpe 4/29/2018

from newsapi import NewsApiClient
from datetime import date, datetime, timedelta
from dateutil.tz import tzutc,tzlocal
import unicodedata
import textwrap

newsapi = NewsApiClient(api_key='MY_API_KEY')

today = date.today()
yesterday = today - timedelta(7)
fromdate = yesterday.strftime('%Y-%m-%d')

# results from "get_everything" are always stale
# top_headlines = newsapi.get_everything(sources='associated-press', from_param=fromdate)

top_headlines = newsapi.get_top_headlines(country='us', category='general')

print "ZCZC AP NEWS", today.strftime('%Y-%m-%d')
a = []
for art in top_headlines['articles']:
    if art not in a:
        a.append(art)
for art in a:
    # newsapi's timestamps are UTC strings, so parse them, convert to localtime, then re-format
    published = datetime.strptime(art['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tzutc())
    block = "%s %s" %(published.astimezone(tzlocal()).strftime('%m/%d %H:%M'), 
        art['title'].replace('...', ''))
    block = unicodedata.normalize('NFKD', unicode(block)).encode('ascii', 'ignore')
    indent = 4
    fmtblock = '\n'.join(textwrap.wrap(block, width=66, initial_indent='', subsequent_indent=' '*indent))
    print fmtblock+'\n'
print "NNNN"
