#!/usr/bin/python
# Web callback for flowroute SMS api

import sys, os, json, subprocess, time, datetime, sqlite3

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
                            
# read json from POST request.
try:
    blob = sys.stdin.read(int(os.environ['CONTENT_LENGTH']))
    myjson = json.loads(blob)
except:
    sys.stdout.write("CGI called without CONTENT_LENGTH, or otherwise unparseable input.\r\n%s\r\n" % (blob) )
    sys.stdout.flush()
    sys.exit(1)

# Send success output, content doesn't matter
print 'Content-Type: application/json\n\n'
result = {'success':'true','message':'Received'};
print json.dumps(result) 

# sender doesn't need weird processing because it will always be a phone number i hope.
sender = myjson['from'].encode('ascii', 'ignore')
# Turn the broken two-char surrogate codepoint representations from Flowroute into
# single unicode chars so we can look them up. 
body = myjson['body'].encode('utf-16', 'surrogatepass').decode('utf-16')

# Replace all emoji in the message body with their textual descriptions between :'s.
s = ''
for c in body:
    if ord(c) > 255:
        s = s + ':' + unicode_char_to_name(ord(c)) + ':'
    else:
        s = s + c

body = s


# Log all the details in case it screws up.
try:
	with open('/tmp/postlog', 'a') as f: 
		f.write(time.ctime())
		f.write("\r\n")
		f.write(json.dumps(myjson))
		f.write("\r\n")
		f.write(body)
		f.write("\r\n")
except:
	pass

datestring = time.strftime("%H:%M, %a %b %e %Y")
# '18:37, Mon Aug  1 2016'

message = chr(7)+chr(7)+chr(7)+"\r\nZCZC SMS FROM %s AT %s\r\n%s\r\nNNNN\r\n" % (sender, datestring, body)
# Pad out the message with 62 spaces and 2 bells to eject enough tape from the reperf
# to be able to tear off the whole message. 
# message = message + ' '*62 + chr(7) + chr(7) + '\r\n'
message = message + '\r\n'

# Subprocess will choke on anything that's not plain ascii, apparently, so clean up.
message = message.encode('ascii', 'ignore')

# The queue file should start with R to go to the reperf or T to go to the M28
try:
        qfile = '/var/spool/tty/T%s' %(datetime.datetime.now().strftime("%s_%f"))
        with open(qfile, 'w') as f:
                f.write(message)
except:
        cmd = "mail -s from_flowroute_sms eric@limpoc.com"
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout_data = p.communicate(input=message)[0]

