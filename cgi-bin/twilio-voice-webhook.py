#!/usr/bin/python
# callback cgi for Twilio incoming voice call 
# To use this you have to configure a twilio phone number to use a TwiML bin on 
# incoming voice calls, which should contain:
#<?xml version="1.0" encoding="UTF-8"?>
#<Response>
#    <Record timeout="10" transcribe="true" transcribeCallback="http://tty.limpoc.com/cgi-bin/twitranscribe" maxLength="120" />
#</Response>

import sys, os, subprocess, time, datetime, urlparse, re, textwrap

try:
    postblob = sys.stdin.read(int(os.environ['CONTENT_LENGTH']))
except:
    sys.stdout.write("CGI called without CONTENT_LENGTH, or otherwise unparseable input.\r\n");
    sys.stdout.flush()
    sys.exit(1)


print 'Content-Type: application/xml\n\n'
print '''<?xml version="1.0" encoding="UTF-8" ?>
<Response>
</Response>
'''
# turn the blob of encoded POST data into useful key/value pairs.
params = urlparse.parse_qs(postblob)

if 'From' in params:
	sender = params['From'][0].encode('ascii', 'ignore')
	sender = re.sub('\+', '', sender) # strip off unprintable + sign
else:
	sender = 'unknown sender'

if 'TranscriptionText' in params:
	body = params['TranscriptionText'][0].encode('ascii', 'ignore')
	body = textwrap.fill(body, 70)
else:
	body = 'empty message'

if 'Caller' in params:
	callername = params['Caller'][0]
else:
	callername = ''

datestring = time.strftime("%H:%M, %a %b %e %Y")

# there needs to be a space between multiple cr/lfs because there's a bug in telepipe i think.
if callername:
	message = "ZCZC VOICEMAIL\r\nFROM %s (%s) AT %s\r\n \r\n%s\r\n \r\nNNNN\r\n" % (sender, callername, datestring, body)
else:
	message = "ZCZC VOICEMAIL\r\nFROM %s AT %s\r\n \r\n%s\r\n \r\nNNNN\r\n" % (sender, datestring, body)

alldata = ""
for p in params:
	alldata = alldata + "%s:\t%s\r\n" % (p, params[p][0])

# Log all the details in case it screws up.
try:
	with open('/tmp/twitranscribe.log', 'a') as f: 
		f.write(time.ctime())
		f.write("\r\n")
		f.write(postblob)
		f.write("\r\n")
		f.write(alldata)
		f.write("\r\n")
		f.write(message)
except:
	pass

try: 
	qfile = '/var/spool/tty/T%s' %(datetime.datetime.now().strftime("%s_%f"))
	with open(qfile, 'w') as f:
		f.write(message)
except:
	cmd = "mail -s from_twilio eric@limpoc.com"
	p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	stdout_data = p.communicate(input=message)[0]
