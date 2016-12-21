#!/usr/bin/python
# callback cgi for Twilio incoming SMS webhook

import sys, os, subprocess, time, sqlite3, urlparse, re, datetime

def unicode_char_to_name(ch):
    conn = sqlite3.connect('/opt/ttycommands/uninames.db')
    c = conn.cursor()
    try:
        c.execute('SELECT name FROM uninames WHERE value = ?', (str(ch),))
        name = c.fetchone()[0]
    except:
        name = 'unidentified character'
    conn.close()
    return name

try:
    postblob = sys.stdin.read(int(os.environ['CONTENT_LENGTH']))
except:
    sys.stdout.write("CGI called without CONTENT_LENGTH, or otherwise unparseable input.\r\n");
    sys.stdout.flush()
    sys.exit(1)

# Tell twilio we're happy.
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

if 'Body' in params:
	body = params['Body'][0]
else:
	body = 'empty message'

if 'FromCity' in params and 'FromState' in params and 'FromCountry' in params:
	location = '%s, %s, %s' % ( params['FromCity'][0], params['FromState'][0],params['FromCountry'][0])
	location = location.encode('ascii', 'ignore')
else:
	location = ''

# Replace all emoji in the message body with their textual descriptions between :'s.
s = ''
body = unicode(body, 'utf-8')
for c in body:
    if ord(c) > 255:
        s = s + ':' + unicode_char_to_name(ord(c)) + ':'
    else:
        s = s + c
body = s


datestring = time.strftime("%H:%M, %a %b %e %Y")

if location:
	message = "ZCZC SMS FROM %s IN %s\r\n%s\r\n%s\r\nNNNN\r\n" % (sender, location, datestring, body)
else:
	message = "ZCZC SMS FROM %s AT %s\r\n%s\r\nNNNN\r\n" % (sender, datestring, body)

# Pad out the message with 62 spaces and 2 bells to eject enough tape from the reperf
message = message + ' '*62 + chr(7) + chr(7) + '\r\n'

alldata = ""
for p in params:
	alldata = alldata + "%s:\t%s\r\n" % (p, params[p][0])

# Log all the details in case it screws up.
try:
	with open('/tmp/postlog2', 'a') as f: 
		f.write(time.ctime())
		f.write("\r\n")
		f.write(postblob)
		f.write("\r\n")
		f.write(alldata)
		f.write("\r\n")
		f.write(message)
except:
	pass

# The queue file should start with R to go to the reperf or T to go to the M28
try: 
        qfile = '/var/spool/tty/R%s' %(datetime.datetime.now().strftime("%s_%f"))
        with open(qfile, 'w') as f:
                f.write(message)
except:
        raise
        cmd = "mail -s from_twilio_sms eric@limpoc.com"
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout_data = p.communicate(input=message)[0]

