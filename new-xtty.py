#!/usr/bin/python
# $Id: xtalk.py,v 1.2 2006/10/06 12:30:42 normanr Exp $
import sys,os,xmpp,time,select
#import xml.etree.ElementTree as et
import socket

class Bot:

    def __init__(self,jabber,remotejid):
        self.jabber = jabber
        self.remotejid = remotejid

    def register_handlers(self):
        self.jabber.RegisterHandler('message',self.xmpp_message)
        self.jabber.RegisterHandler('presence',self.xmpp_presence)

    def tty_send(self, msg):
	if not relaymode:
            outbound = str(msg.decode('ascii', 'ignore'))
            outbound = outbound.replace('@', '/')
            if not outbound.endswith('\r'):
                outbound = outbound + '\r\n'
            teletype.send(outbound)
	else:
            print "relaymode, suppressing output:", msg

    # This is the handler that gets registered with the XMPP client for
    # handling incoming messages to us; clean it up and send it to HM for
    # delivery to the teletype loop. Thank god HM does half duplex echo
    # suppression.
    def xmpp_message(self, con, event):
	#print event
        type = event.getType()
        fromjid = event.getFrom().getStripped()
	print "got msg type", type, "from", fromjid, "tojid=", tojid, "listening_to", self.remotejid
        #if type in ['message', 'chat', None] and fromjid == self.remotejid:
        if type in ['message', 'chat', None] and fromjid == tojid:
	    try:
		#outbound = str(event.getBody().decode('ascii', 'ignore'))
		#print 'xmpp->tty:', outbound
		self.tty_send(':'+event.getBody())
	    except: 
		pass
            
    # handle contacts coming on/off line
    def xmpp_presence(self, con, event):
	print event
	nick=event.getFrom().getStripped()
	ttymsg=''
	# keep track of who's on/offline
	if event.getType() == 'unavailable':
            if nick in roster:
                roster.remove(nick)
            ttymsg = nick + " offline."
	else:
            if nick in roster:
                print "got presence event for logged in user", nick
            else:
                roster.append(nick)
                ttymsg = nick + " online."

	# if this message is about us, ignore it to save printing time.
	if nick == 'teletweety@wtrc.net':
            ttymsg = ''

	# if we have anything to print, print it.
	if ttymsg:
            print ttymsg
            self.tty_send(ttymsg)

    def stdio_message(self, message):
        m = xmpp.protocol.Message(to=self.remotejid,body=message,typ='chat')
        self.jabber.send(m)
        pass

    def xmpp_connect(self):
        con=self.jabber.connect()
        if not con:
            sys.stderr.write('could not connect!\n')
            return False
        # sys.stderr.write('connected with %s\n'%con)
        auth=self.jabber.auth(jid.getNode(),jidparams['password'],resource=jid.getResource())
        if not auth:
            sys.stderr.write('could not authenticate!\n')
            return False
        # sys.stderr.write('authenticated using %s\n'%auth)
        self.register_handlers()
        return con

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print "Syntax: xtty JID"
        sys.exit(0)

    print "running as", sys.argv[0]
    if sys.argv[0].endswith('xttyrelay.py'):
    	relaymode = True
    else:
	relaymode = False

    roster = []
    tojid=sys.argv[1].lower()
    # for convenience, so we can call it from a tty commandline
    # without having to escape an @ sign and type a whole jid.
    jids = { 'user1' : 'user1@domain.net', 
	     'user2' : 'somebody@someserver.com' }
    if tojid in jids:
	tojid = jids[tojid]
    print "tojid=", tojid

    # open connection to heavymetal to talk to the tty.
    teletype = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    teletype.connect(('127.0.0.1', 11123))
    
    jidparams={ 'jid': 'teletweety@wtrc.net/TTY', 'password': 'heepy' }
    
    jid=xmpp.protocol.JID(jidparams['jid'])
    cl=xmpp.Client(jid.getDomain(),debug=[])
    
    bot=Bot(cl,tojid)

    if not bot.xmpp_connect():
        sys.stderr.write("Could not connect to server, or password mismatch!\n")
        sys.exit(1)

    cl.sendInitPresence()

    socketlist = {cl.Connection._sock:'xmpp',teletype:'tty'}
    online = 1

    while online:
        (i , o, e) = select.select(socketlist.keys(),[],[],1)
        for each in i:
            if socketlist[each] == 'xmpp':
                cl.Process(1)
            elif socketlist[each] == 'tty':
                msg = teletype.recv(256).rstrip('\r\n')
		tosend = str(msg.decode('ascii', 'ignore')).replace('TTY1: ', '')
		tosend = tosend.replace('', '<bell>')  # bell is "not well formed xml" hahaha.
		tosend = tosend.replace('	', '  ')  # tabs make whole message fail silently
		# need a way to bail out from the tty.

		if not tosend.startswith('/'):
                    # we have a message from the TTY loop, so hand it to the 
                    # XMPP client for transmission.
                    # bot.stdio_message(str(msg.decode('ascii', 'ignore')))
                    print "tty->xmpp:", tosend
                    bot.stdio_message(tosend)
		else:
                    # process / commands form the tty, like who and quit.
                    if tosend.lower().startswith("/quit"):
                        bot.tty_send('xmpp closed.')
                        sys.exit()

                    if tosend.lower().startswith("/who"):
                        list = ', '.join(roster)
                        bot.tty_send(list)

                    if tosend.lower().startswith("/to"):
                        elem = tosend.lower().split()
                        if len(elem) > 1:
                            tojid = elem[1]
                            print "tojid=", tojid
                            if tojid in jids:
                                tojid = jids[tojid]
                        print "new tojid=", tojid
                        bot=Bot(cl,tojid) ## reregister with new destination
                        # this doesn't change self.remotejid in the xmpp handlers,
                        # because i don't understand python scoping
                        bot.tty_send('talking to ' + tojid )
            else:
		# something weird came from select(), shouldn't happen
                raise Exception("Unknown socket type: %s" % repr(socketlist[each]))
    cl.disconnect()


