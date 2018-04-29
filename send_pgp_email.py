#! /usr/bin/env python
# 
import sys
import smtplib
import subprocess

from email.mime.text import MIMEText

# set these to real values. Sender_address is just what will show up as the "from" 
# address in email. "sign_user" should be a passwordless secret gpg key in the local
# user's secret key list, which will be used to sign outgoing emails. 

sender_address = "my_email@wherever.com"
sign_user = 'my_key'

if len(sys.argv) < 3:
    print "usage: email recipient subject . . ."
    sys.exit(1)

blob = sys.stdin.read()

# try to feed the message body to gpg to encrypt. This will fail
# if there is no public key stored that matches the specified recipient

p = subprocess.Popen(['/usr/bin/gpg2', '-sea', '-u', sign_user, '-r', sys.argv[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
result = p.communicate(input=blob)
if result[0]:
    cryptblob = result[0]
else:
    cryptblob = '[empty message]'

if p.returncode != 0:
    print "error trying to encrypt, nothing sent"
    if result[1]:
        print result[1]
    sys.exit(0)

msg = MIMEText(cryptblob)
msg['Subject'] = ' '.join(sys.argv[2:])
msg['From'] = sender_address
msg['To'] = sys.argv[1]

try:
    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()
except:
    print "Send failed."
    sys.exit(1)

print "Email submitted."
sys.exit(0)
