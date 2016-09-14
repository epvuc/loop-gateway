#! /usr/bin/python
import json
import urllib2
import base64
from pprint import pprint
import sys

# This program reads a phone number and SMS message from stdin and tries to deliver
# it to the recipient via Flowroute.com's SMS API. You can sign up for a Flowroute
# account at https://www.flowroute.com/. The service is very, very cheap and works
# very well for both sending and receiving SMS. 
#
# It can be invoked two ways: 
# 1. destination phone number and entire message on command line
# 2. destination phone number on the command line, message body on subsequent
#    lines. See the command definitions in ser.py for details. 
#
# To receive incoming SMS messages, you need something to accept incoming SMS 
# from the provider -- see the /opt/ttycommands/cgi-bin directory. 

# fill in your flowroute phone number, userid, and password here:
mynumber = 'MY_FLOWROUTE_PHONE_NUMBER''
user = 'MY_FLOWROUTE_USER_ID'
password = 'MY_FLOWROUTE_PASSWORD'

# if there's only one arg and it looks like a number, use it as destination and
# read message body via stdin, for executing directly from within HeavyMetal
# If there's 2 or more args, assume it's a phone number then a message all on
# the commandline, for executing as a command defined in heavymetal.cfg

if len(sys.argv) == 2:
	if sys.argv[1].isdigit():
		body = sys.stdin.read().rstrip()
	else: 
		print "Usage: send_sms phonenumber message la la etc stuff and things"
		sys.exit(0)
else:
	if len(sys.argv) < 3: 
		print "Usage: send_sms phonenumber message la la etc stuff and things"
		sys.exit(0)
	else: 
		body = ' '.join(sys.argv[2:])

data = { 'from': mynumber, 'to': sys.argv[1], 'body': body }

base64string = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
req = urllib2.Request('https://api.flowroute.com/v2/messages')
req.add_header("Authorization", "Basic %s" % base64string)
req.add_header("Content-Type", "application/json")
try:
	result = urllib2.urlopen(req, json.dumps(data))
except urllib2.HTTPError as e:
	if e.code == 403:
		print "SEND FAILED: BAD SMS PARAMS"
	else: 
		if e.code == 401:
			print "SEND FAILED: BAD CREDENTIALS"
		else: 
			print "SEND FAILED: ", e.code
else:
	print "SMS SENT"
