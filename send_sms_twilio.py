#! /usr/bin/python
# Send an SMS using the Twilio rest API
#
# This program reads a phone number and SMS message from stdin and tries to deliver
# it to the recipient via Twilio.com's SMS API. You can sign up for a Twilio
# account at https://www.twilio.com/. The service is cheap for SMS and works well
# well for both sending and receiving SMS, as well as transcribing incoming voice
# messages. (see /opt/ttycommands/cgi-bin/twitranscribe) 
#
# It can be invoked two ways: 
# 1. destination phone number and entire message on command line
# 2. destination phone number on the command line, message body on subsequent
#    lines. See the command definitions in ser.py for details. 
#
# To receive incoming SMS messages, you need something to accept incoming SMS
# from the provider -- see the /opt/ttycommands/cgi-bin directory.

import json
import urllib,urllib2
import base64
import sys

# Fill in auth info from Twilio here:
mynumber = '+MY_TWILIO_PHONE_NUMBER'
account_sid = 'MY_TWILIO_ACCOUNT_SID'
auth_token = 'MY_TWILIO_AUTH_TOKEN'

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

data = { 'From': mynumber, 'To': '+'+sys.argv[1], 'Body': body }
postdata = urllib.urlencode(data)

base64string = base64.encodestring('%s:%s' % (account_sid, auth_token)).replace('\n', '')
req = urllib2.Request('https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json' %(account_sid))
req.add_header("Authorization", "Basic %s" % base64string)
req.add_header("Content-Type", "application/x-www-form-urlencoded")
try:
	result = urllib2.urlopen(req, postdata)
	# print result.read()

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
