#! /usr/bin/python
import time
import unicodedata
import re
import sys, os
import socket
from datetime import datetime
from dateutil import tz,parser
import argparse
import subprocess

#
# This program takes arbitrary input, makes it vaguely teletype-compatible
# by substituting out unprintable characters and avoiding too-long lines and
# overstrikes, and then delivers it via tcp to the ser.py process for printing
# to the TTY loop, waiting until printing is complete before terminating. 
#
# If called with "-p" it will attempt to use a serially attached X10 controller
# to power the machine on before printing and off after printing. 
# For this to work you'll need to look at line 126 and following and tell it
# the /dev device name the X10 bottlerocket transmitter appears at, and the 
# housecode and device number. 

# halfassed attempt to match "any" url, since we don't want to print them
# see http://daringfireball.net/2010/07/improved_regex_for_matching_urls
GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')


LTRS = ( 'E', 'A', 'S', 'I', 'U', 'D', 'R', 'J', 'N', 'F', 'C', 'K', 
         'T', 'Z', 'L', 'W', 'H', 'Y', 'P', 'Q', 'O', 'B', 'G', 'M', 'X', 'V')

FIGS = ( '3', '-', '8', '7', '$', '4', '\'', ',', '!', ':', '(', '5', 
         '"', ')', '2', '#', '6', '0', '1', '9', '?', '&', '.', '/', ';')

class Teletype:
    """ teletype interface, try to turn tweets into something
    printable on a teletype machine"""

    def __init__(self, hmhost):
        self.edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
                       ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!') ]
        self.baudrate = 45.45
        # initialize backlog management data
        self.last_sent = 0
        self.expected_done = 0
        self.backlog = 0
	self.max_backlog = 6
        # establish a connection to the teletype machine.
        self.ttysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ttysock.connect(hmhost)
        print "connected."

    # general purpose line splitter to avoid overstriking
    def linewrap(self, blob, width=72):
        lines = blob.splitlines()
        new = []
        for l in lines:
            while True:
                if len(l) > width:
                    new.append(l[:width])
                    l = l[width:]
                else:
                    new.append(l)
                    break
        return '\r\n'.join(new) + '\r\n'

    def debugprint(self, text):
        foo = text.replace('\n', '[LF]\n')
        foo = foo.replace('\r', '[CR]\r')
        print foo

    def ttypreprint(self, text):
        self.ttysock.sendall(text.upper())

    def ttyprint(self, text):
        # strip out anything that looks like a URL, maybe?
        text = re.sub(GRUBER_URLINTEXT_PAT, "URL", text)

        # construct the whole block to be printed
        for (orig, repl) in self.edits:
            text = text.replace(orig, repl)
        #text = self.linewrap(text, 72)

        # send the text and block until the remote end acks our
        # shutdown of the socket, which will only happen once the
        # tty has stopped printing. it's sort of weird that this
        # works. 
        self.ttysock.sendall(text.upper())
        self.ttysock.shutdown(socket.SHUT_WR)
        while True:
            data = self.ttysock.recv(1024)
            if not data:
                break
        self.ttysock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Feed text to teletype.')

    parser.add_argument('-p', '--power', dest='power', action='store_const',
                    const=True, default=False,
                    help='Control teletype power.')

    parser.add_argument('-r', '--reperf', dest='which', action='store_const',
                    const='reperf', default='m28',
                    help='Control teletype power.')
    args = parser.parse_args()

    l = sys.stdin.read()

    if os.path.exists('/tmp/ttylock'):
        print "TTY is locked, diverting to mail."
        cmd = "mail -s missed_tty_message eric@limpoc.com"
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout_data = p.communicate(input=l)[0]
        sys.exit()

    with open('/tmp/ttylock', 'a') as f:
        f.write('tty in use\r\n')

    #args.power = False
    #print "Power on/off disabled for testing!"

    if args.power:
        # Turn on the machine.
        if args.which == 'reperf':
            on_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O2', 'on']
            off_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O2', 'off']
            startdelay = 7
        else:
            on_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O1', 'on']
            off_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O1', 'off']
            startdelay = 2
        try:
            p = subprocess.Popen(on_cmd)
            time.sleep(startdelay) # let motor spin up
        except:
            print "Failed to power on teletype, proceeding anyway."



    # feed the text block to the teletype via HeavyMetal
    # this is crappy.
    tty = Teletype(hmhost=('127.0.0.1', 11123))
    if args.which == 'reperf' and args.power:
        tty.ttypreprint('      \r\n')
        time.sleep(1)
    tty.ttyprint(l)

    if args.power:
        time.sleep(2) # be safe
        try:
            p=subprocess.Popen(off_cmd)
            time.sleep(2)
            p=subprocess.Popen(off_cmd)
            time.sleep(2)
            p=subprocess.Popen(off_cmd)
        except:
            print "Failed to power off teletype, finishing anyway."
            
    os.remove('/tmp/ttylock')
