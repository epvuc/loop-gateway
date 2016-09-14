#! /usr/bin/python
# coding=utf8
import praw
import time
import textwrap
import sys
import unicodedata
import re

#
# This program will connect to Reddit using the public API and fetch the
# top few posts and responses from the requested subreddit, formatting them
# for teletype and outputting them via stdout. It can be invoked by a command
# definition in ser.py so that its output is printed to the loop. 
# Note: it is slow, and produces a lot of output, so it will keep the machine
# printing for a long time, usually. 
#

# halfassed attempt to match "any" url, since we don't want to print them
# see http://daringfireball.net/2010/07/improved_regex_for_matching_urls
GRUBER_URLINTEXT_PAT =  re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')

# Character substitutions when printing to the teletype.
edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
          ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!'), 
	  ('&amp;', '&'), ('&gt;', ')'), ('&lt;', '(') ]

class TeleReddit():
        """reddit for teletype"""
        def __init__(self, user_agent='redditype', login='', password=''):
                self.r = praw.Reddit(user_agent=user_agent)
                if login and password:
                        try:
                                r.login(self.login, self.password)
                        except:
                                sys.stderr.write('login failed for user '+self.login+'\n')
                        print 'logged in'

        def ttyprint(self, body=u'', width=65, indent=0):
                """pretty print a block of text suitable for teletype output"""

                # the teletype can not take unicode characters, or even full ascii
                # python really does not deal well with this at all.
                # body = unidecode.unidecode(body)
                body = unicodedata.normalize('NFKD', body).encode('ascii','ignore')
                for (orig, repl) in edits:
                        body = body.replace(orig, repl)
		body = re.sub(GRUBER_URLINTEXT_PAT, "(URL)", body)
                sys.stdout.write( '\n'.join(textwrap.wrap(body, width=width, 
                                                initial_indent=' '*indent, 
                                                subsequent_indent=' '*indent)))
                sys.stdout.write('\r\n')

        def printcomments(self, sub, max=5): 
                """pretty print the comments attached to a Submission object"""
                fc = praw.helpers.flatten_tree(s.comments)
                i = 1
                for comm in fc:
                        if hasattr(comm, "body"):
                                tr.ttyprint( unicode(i) + u" : " + unicode(comm.author))
                                tr.ttyprint (body=comm.body, width=60, indent=6)
                                i = i + 1
                        if i > max:
                                break
        
if __name__ == "__main__":

        maxsubmissions = 5
        maxcomments = 5
	skipstickies = True

        try: 
                mysub = sys.argv[1]
        except:
                mysub = "AskReddit"

        tr = TeleReddit()

        newsubmissions = tr.r.get_subreddit(mysub).get_hot(limit=maxsubmissions)
        for s in newsubmissions:
		if skipstickies and s.stickied:
			continue
                tr.ttyprint(u"Created by " + unicode(s.author) + u" " + \
                            time.strftime("%a %d-%b-%y %H:%M", time.gmtime(s.created)) )
                tr.ttyprint(s.title + u'\n')
		if hasattr(s, "selftext"):
			if s.selftext != "":
				tr.ttyprint(u'\n')
				tr.ttyprint(s.selftext + u'\n')
				tr.ttyprint(u'\n')
		if hasattr(s, "comments"):
                	tr.ttyprint(unicode(s.num_comments) + u" comments, "+ unicode(s.ups)+ u" upvotes\n")
                	tr.printcomments(sub=s, max=5)
		else:
			tr.ttyprint("no comments, "+ unicode(s.ups)+ u" upvotes\n")
                tr.ttyprint( u"-----------------------------------------------------")
