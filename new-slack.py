#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program connects to Slack using the XMPP interface, for which you need to use
# Slack's website to find the necessary JID (userid) and password, and the correctly
# formatted names of the team/room/whatever you want to take part in. 
# 
# Invocation will look something like this: 
# 
# /opt/ttycommands/new-slack.py -j USERNAME@TEAMNAME.xmpp.slack.com -p TEAMNAME.XMPP_PASSWORD -r ${ROOM}@conference.TEAMNAME.xmpp.slack.com -n USERNAME
# 
# Once invoked it will connect via tcp to the ser.py process on port 11123 and relay chat 
# between the teletype loop and Slack. 
#
# Commands pertinent to the slack interface start with /: 
#   /quit  -  exit this program and log out
#   /msg USERNAME  -  send a private message to username. 


import sys
import logging
import getpass
from optparse import OptionParser

import sleekxmpp
import time

import socket,select,os,re


# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
##if sys.version_info < (3, 0):
    #from sleekxmpp.util.misc_ops import setdefaultencoding
    #setdefaultencoding('utf8')
#else:
    #raw_input = input

# halfassed attempt to match "any" url, since we don't want to print them
# see http://daringfireball.net/2010/07/improved_regex_for_matching_urls
#GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
# this one is newer, from https://gist.github.com/gruber/249502
GRUBER_URLINTEXT_PAT =  re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')

# Character substitutions when printing to the teletype.
edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
          ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!') ]


class MUCBot(sleekxmpp.ClientXMPP):

    """
    Adapter to connect slack to a teletype machine server. 
    """

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

        # The groupchat_presence event is triggered whenever a
        # presence stanza is received from any chat room, including
        # any presences you send yourself. To limit event handling
        # to a single room, use the events muc::room@server::presence,
        # muc::room@server::got_online, or muc::room@server::got_offline.
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)

        self.add_event_handler("message", self.priv_message)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
#       self.get_roster()   # this times out for some reason.
        self.send_presence()
	print "***** trying to join"
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        # If a room password is needed, use:
                                        # password=the_room_password,
                                        wait=True)

    def tty_send(self, msg):
        outbound = str(msg.decode('ascii', 'ignore'))
        # don't bother printing URLs!
        outbound = re.sub(GRUBER_URLINTEXT_PAT, "URL", outbound) 
        # Apply character replacements... 
        for (orig, repl) in edits:
            outbound = outbound.replace(orig, repl)
        if not outbound.endswith('\n'):
            outbound = outbound + '\n'
        teletype.send(outbound)

    def muc_message(self, msg):
        """
        handle groupchat messages coming from xmpp.
        """
        # This is where we end up when a messages comes to us from slack.
        #for k in msg.keys():
        #   print "   ", k,"=",msg[k]

        # Don't send delayed (queued) messages to the teletype, it takes too long
        if 'delay' in msg.keys():
            print "Delayed message: <%s> %s" % (msg['mucnick'], msg['body'])
        else:
            if msg['mucnick'] != self.nick:
		print "<%s> %s" % (msg['mucnick'], msg['body'])
                self.tty_send("(%s) %s" % (msg['mucnick'], msg['body']))

    def priv_message(self, msg):
        """
        handle non-groupchat messages from xmpp.
        """
        if msg['mucroom'] != "":
               print "- priv_message discarding muc message."
        else:
            sender = str(msg['from']).split('@')[0]
            if 'delay' in msg.keys():
                print "Delayed message: <%s> %s" % (sender, msg['body'])
            else:
                # this is halfassed, but if tty sends a /m sometimes it comes back? i dunno.
                if sender != self.nick: 
                    # Do send delayed (queued) private messages to the teletype, we probably want them
                    # actually it doesn't seem to ever notice they've been read. nevermind.
                    print "-%s- %s" % (sender, msg['body'])
                    self.tty_send("\007-%s- %s" % (sender, msg['body']))

                
    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.

        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        if presence['muc']['nick'] != self.nick:
		print "Got presence for", presence['muc']['nick']
            #self.send_message(mto=presence['from'].bare,
                              #mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      #presence['muc']['nick']),
                              #mtype='groupchat')


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join")
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.room is None:
        opts.room = raw_input("MUC room: ")
    if opts.nick is None:
        opts.nick = raw_input("MUC nickname: ")

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(opts.jid, opts.password, opts.room, opts.nick)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.register_plugin('xep_0203') # Delayed delivery


    # open connection to heavymetal to talk to the tty.
    teletype = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    teletype.connect(('127.0.0.1', 11123))
    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        xmpp.process(block=False)
        teletype.send("connected to %s\n" %(opts.room.split('@')[0]))
        # now sit in a select loop waiting for stuff we should send to xmpp
#	socketlist = { sys.stdin:'stdio', teletype: 'tty' }
	socketlist = { teletype: 'tty' }
	online = 1
	while online:
            (i, o, e) = select.select(socketlist.keys(),[],[],1)
            for each in i: 
#                if socketlist[each] == 'stdio':
#                    tosend = sys.stdin.readline().rstrip('\r\n')
#                    if not tosend.lower().startswith("/q"):
#                        xmpp.send_message(mto=opts.room, mbody=tosend, mtype='groupchat')
#                    else:
#                        if tosend.lower().startswith("/q"):
#                            online = 0

                if socketlist[each] == 'tty':
                    msg = teletype.recv(256).rstrip('\r\n')
                    tosend = str(msg.decode('ascii', 'ignore')).replace('TTY1: ', '')
                    tosend = tosend.replace('^G', '<bell>')  # bell is "not well formed xml" hahaha.
                    tosend = tosend.replace('       ', '  ')  # tabs make whole message fail silently
                    if not tosend.startswith('/'):
                        xmpp.send_message(mto=opts.room, mbody=tosend, mtype='groupchat')
                    else:
                        cmd = tosend.split()
                        # /msg command
                        if (cmd[0].lower() == '/m' or cmd[0].lower() == '/msg') and len(cmd) > 2:
                            recip = cmd[1].lower()
                            body = ' '.join(cmd[2:])
                            # need to derive correct target jid from just the /m arg, if possible
                            try: 
                                jid = re.findall('.*?@(.*?)(?:/|$)', opts.jid)[0]
                            except:
                                jid = ''
                            print "Privmsg to %s@%s: %s" % (recip, jid, body)
                            xmpp.send_message(mto='%s@%s' % (recip, jid), mbody=body, mtype='chat')

                        # /quit command
                        if cmd[0].lower() == '/q' or cmd[0].lower() == '/quit':
                            online = 0

        print "Trying to exit...."
        xmpp.disconnect()
        teletype.send("disconnected.\n")
        sys.exit()

    else:
        print("Unable to connect.")
        teletype.send("connect failed.\n")
        sys.exit()
