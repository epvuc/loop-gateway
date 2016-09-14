#! /usr/bin/env python
import sys
import smtplib
from email.mime.text import MIMEText

# This program is meant to be invoked from a ser.py command definition
# so that it can be run from the teletype loop. Destination email address
# and subject line are specified on the command line, and the body of the
# message is supplied on subsequent lines, followed by NNNN. 

# Fill in the return address you want your emails to come from below:
sender_address = "MY_EMAIL_ADDRESS"

if len(sys.argv) < 3:
    print "usage: email recipient subject . . ."
    sys.exit(1)

blob = sys.stdin.read()
msg = MIMEText(blob)
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
