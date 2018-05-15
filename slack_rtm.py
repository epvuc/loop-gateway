#! /usr/bin/python
# -*- coding: utf-8 -*-
# Slack client for teletype, using slack RTM API
# meant to work with ser.py for interfacing with teletypes.
# epv 4/20/2018

import os, time, sys, select, socket, re
from slackclient import SlackClient
from pprint import pprint
import unicodedata

# Slack login credential, obtained via:
# https://get.slack.help/hc/en-us/articles/215770388-Create-and-regenerate-API-tokens
slack_token = "MY_SLACK_TOKEN"

# your Slack "team" should include this channel.
default_channel = 'MY_DEFAULT_CHANNEL'


GRUBER_URLINTEXT_PAT =  re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')

# Character substitutions when printing to the teletype.
edits = [ ('@', '(at)'), ('<', '('), ('>', ')'), ('%', '(pct)'), ('=', '(eq)'),
                    ('[', '('), (']', ')'), ('+', '.'), ('_', '-'), ('|', '!') ]
def tty_send(msg):
    outbound = unicodedata.normalize('NFKD', unicode(msg)).encode('ascii', 'ignore')
    # outbound = str(msg.decode('ascii', 'ignore'))
    outbound = re.sub(GRUBER_URLINTEXT_PAT, "URL", outbound)
    for (orig, repl) in edits:
        outbound = outbound.replace(orig, repl)
    if not outbound.endswith('\r'):
        outbound = outbound + '\r'
    teletype.send(outbound + '\n')

def slack_userid_to_username(u):
    try:
	upro = sc.api_call('users.profile.get', user=u)
        username = upro['profile']['display_name_normalized']
        if username == "":
            username = upro['profile']['real_name_normalized']
    except:
        username = u
    return username

def slack_channelid_to_channelname(c):
    if c is None:
        return None
    if c.startswith('C'):
        try:
            channel_info = sc.api_call('channels.info', channel=c)
            channel_name = channel_info['channel']['name']
        except:
            channel_name = None
    else:
        try:
            group_info = sc.api_call('groups.info', channel=c)
            channel_name = group_info['group']['name']
        except:
            channel_name = None
    return channel_name

def slack_channelname_to_channelid(n):
    # should probably cache this instead of checking every time but enh.
    print 'looking up channelid for', n
    chan = sc.api_call("channels.list")
    cmap = {}
    for c in chan['channels']:
        cmap[c['name']] = c['id']
        cmap[c['name'].lower()] = c['id']
    if cmap.get(n):
        print 'returning channelid', cmap.get(n), 'for channel', n
        return(cmap.get(n))
    else:
        print 'channel', n, 'not found in open channel list, trying groups'
        groups = sc.api_call("groups.list")
        cmap = {}
        for c in groups['groups']:
            cmap[c['name']] = c['id']
            cmap[c['name'].lower()] = c['id']
        if cmap.get(n):
            print 'returning group id', cmap.get(n), 'for channel', n
            return(cmap.get(n))
        else:
            print 'channel', n, 'not found in groups list either, returning null.'
            return False
    
def slack_get_presence(u):
    p = sc.api_call('users.getPresence', user=u)
    if p.get('presence') == 'active':
        return True
    else:
        return False
    
def resolve_ids(m):
    # sometimes the message text has slack userids embedded in it so try to 
    # parse them out, match them to real names, and replace them in the text. 
    print 'resolving', repr(m)
    try:
        for u in re.findall('<@(U\S+)>', m):
            m = re.sub('<@%s>'%(u), '@'+slack_userid_to_username(u), m)
            print m
    except:
        pass
    try:
        for c in re.findall('<#(C\S+)\|\S+>', m):
            m = re.sub('<#%s\|\S+>'%(c), '#'+slack_channelid_to_channelname(c), m)
            print m
        for c in re.findall('<#(C\S+)>', m):
            m = re.sub('<#%s>'%(c), '#'+slack_channelid_to_channelname(c), m)
            print m
    except:
        pass
    return m

def slack_join_channel_or_group(newchannel):
    if newchannel.startswith('C'):
        print 'joining channel', newchannel
        res = sc.api_call('channels.join', channel=newchannel)
    else:
        print 'joining group', newchannel
        res = sc.api_call('groups.open', channel=newchannel)
    if res.get('ok') == True:
        current_channel = newchannel
        return True
    else:
        current_channel = False
        return False

def sl_print(m):
    # print(m)
    tty_send(m)
    
def process_slack_event(r):
    # seems to be a response to sending a message?
    if 'ok' in r:
        if r['ok']:
            #sl_print("!OK")
            pass
        else:
            sl_print( "!I guess something bad happened?-")
        return
    
    pprint(r)
    print "============="
    # this is an incoming actual message. there are tons of weird variations.
    if r['type'] == 'message':
        if r.get('subtype') == 'channel_join':
            # print '!channel_join message'
            return
        if r.get('subtype') == 'channel_leave':
            # print '!channel_leave message'
            return
        # it's funny because you can't delete things printed on a teletype
        if r.get('subtype') == 'message_deleted':
            try:
                user =slack_userid_to_username( r['previous_message'].get('user'))
                print("! message by %s deleted: %s" %(user, resolve_ids(r['previous_message']['text'])))
                sl_print("! message by %s deleted: %s" %(user, resolve_ids(r['previous_message']['text'])))
            except:
                pass
            return

        # sometimes the message text has slack userids embedded in it so try to 
        # parse them out, match them to real names, and replace them in the text. 
        r['text'] = resolve_ids(r.get('text'))

        # only print message sent to the "current" channel, not all subscribed.
        if r.get('channel') != current_channel:
            # (unless it's a direct message)
            if r.get('channel')[0] != 'D':
                return
        if r.get('hidden'):
            print "printing a quoted tweet, probably"
        # sometimes a quoted tweet shows up like this, it's gross, try it and if it works great
            try:
                user = slack_userid_to_username(r.get('message').get('user'))
                attachment = r.get('message').get('attachments')[0]
                attach_text = resolve_ids(attachment.get('text'))
                attach_author = attachment.get('author_name')
                attach_svc = attachment.get('service_name')
                if attach_author and attach_svc:
                    attrib = '(%s/%s) ' % (attach_author, attach_svc)
                else:
                    if attach_author:
                        attrib = '(%s) ' % (attach_author)
                    else:
                        if attach_svc:
                            attrib = '(%s) ' % (attach_svc)
                        else:
                            attrib = ''
                if r.get('channel')[0] == 'D':
                    sl_print('\007-%s- %s %s' % (user, attrib, attach_text))
                else:
                    if re.search('@%s\s+'%my_username, attach_text):
                        attach_text = '\007'+attach_text
                    sl_print('(%s) %s %s' % (user, attrib, attach_text))
            except:
                pprint(r)
                pass
            return
        # at this point we're ready to print
        username = slack_userid_to_username(r.get('user'))
        msg = r.get('text')
        if r['channel'][0] == 'D':
            # private message
	    sl_print( '\007-%s- %s' %(username, msg))
        else:
            # open message
            if re.search('@%s\s+'%my_username, msg):
                msg = '\007'+msg
	    sl_print ('(%s) %s' %(username, msg))
        return

    # member joins channel
    if r['type'] == 'member_joined_channel':
        sl_print( '%s has joined %s' % (slack_userid_to_username(r['user']), slack_channelid_to_channelname(r['channel'])))
        return
    if r['type'] == 'member_left_channel':
        sl_print ('%s has left %s' % (slack_userid_to_username(r['user']), slack_channelid_to_channelname(r['channel'])))
        return

    # i do not want typing notifications or other crap.
    if r['type'] == 'user_typing':
        return
    if r['type'] == 'dnd_updated_user':
        return
    if r['type'] == 'user_change':
        return
    if r['type'] == 'hello':
        sl_print ("slack connected")
        return



# connect to the teletype via ser.py
teletype = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
teletype.connect(('10.0.0.148', 11123))
teletype.send("slack starting\r\n")

online = True
sc = SlackClient(slack_token)
if sc.rtm_connect(auto_reconnect = True):
    print "Connection Succeeded"
    time.sleep(1)
    if sc.server.connected:
        # populate username/id tables for future use.
        uids = {}
        unames = {}
        try:
            users = sc.api_call('users.list')
            for u in users['members']:
                uids[u['name']] = u['id']
                unames[u['id']] = u['name']
        except:
            pass
    # get my own username by passing null argument to users.profile.get
    my_username = slack_userid_to_username('') 

    # try to join the specified channel, or the default one if that fails
    # or isn't speficied.
    current_channel = ''
    if len(sys.argv) > 1:
        newchannel = slack_channelname_to_channelid(sys.argv[1])
        if slack_join_channel_or_group(newchannel):
            current_channel = newchannel
        else:
            current_channel = ''
            sl_print("failed to join %s" % (sys.argv[1]))

    if current_channel == '':
        newchannel = slack_channelname_to_channelid(default_channel)
        if slack_join_channel_or_group(newchannel):
            current_channel = newchannel
        else:
            current_channel = ''
            sl_print('failed to join default channel %s' %(default_channel))
            
    if current_channel == '':
        sl_print("not in a channel. use /j to join one")
    else:
        sl_print("i am %s in channel %s" % (my_username, slack_channelid_to_channelname(current_channel)))
                

    socketlist = { teletype: 'tty' }
    # main select/poll loop. 
    while online and sc.server.connected is True:
        (i, o, e) = select.select(socketlist.keys(),[],[], 0.5)
        for each in i:
            # process select loop events
            if socketlist[each] == 'tty':
                #  tosend = sys.stdin.readline().rstrip('\r\n')
                msg = teletype.recv(256).rstrip('\r\n')
                tosend = str(msg.decode('ascii', 'ignore'))
                tosend = tosend.replace('^G', '<bell>')  # bell is "not well formed xml" hahaha.
                tosend = tosend.replace('	', '  ')  # tabs make whole message fail silently
                # drop blank lines so we don't make a bogus rtm_send_message() call
                if not tosend:
                    continue
                if not tosend.startswith('/'):
                    if current_channel:
                        sc.rtm_send_message(channel=current_channel, message=tosend)
                    else:
                        sl_print("not in a channel")
                else:
                    # process a / command
                    cmd = tosend.split()
                    cmd[0] = cmd[0].lower()
                    if cmd[0] == '/q' or cmd[0] == '/quit':
                        sl_print("quitting slack")
                        online = False
                    # try to send a direct message? this is janky.
                    if (cmd[0] == '/m' or cmd[0] == '/msg') and len(cmd) > 2:
                        recip = cmd[1].lower()
                        body = ' '.join(cmd[2:])
                        if recip in uids:
                            try:
                                # first you need to establish a direct message "channel" which acts
                                # just like a regular channel but it's id starts with D
                                imchan = sc.api_call('im.open', user=uids[recip])
                                dm_id = imchan['channel']['id']
                                # then you can send a message to it just like to an open channel
                                sc.rtm_send_message(channel=dm_id ,message=body)
                            except:
                                sl_print("dm to %s failed." %(recip))
                                raise
                        else:
                            sl_print("no such user")
                            
                    # /j, /join - join a channel. I think you can be in more than one at a time.
                    # when we send channel messages, they only go into the "current" one, which
                    # is the last one you joined. 
                    if (cmd[0] == '/j' or cmd[0] == '/join') and len(cmd) > 1:
                        newchannel = slack_channelname_to_channelid(cmd[1].lower())
                        if not newchannel:
                            sl_print('no such channel')
                            continue
                        if slack_join_channel_or_group(newchannel):
                            print "joined", cmd[1].lower(), "=", newchannel
                            current_channel = newchannel
                            sl_print("joined channel %s" %(cmd[1]))
                        else:
                            sl_print("failed to join %s" % (cmd[1]))
                    # /l, /leave - leave a channel. If you leave all the channels you were in you
                    # can still be connected and get direct messages. I dunno what to do about
                    # where to send open messages or even how to tell which channels we're in.
                    if (cmd[0] == '/l' or cmd[0] == '/leave'):
                        if len(cmd) > 1:
                            leavechannel = slack_channelname_to_channelid(cmd[1].lower())
                            if leavechannel is None:
                                sl_print("unknown channel %s" %(cmd[1]))
                                continue
                        else:
                            leavechannel = current_channel
                        if sc.api_call('channels.leave', channel=leavechannel):
                            current_channel = "" # is this the right thing?
                            sl_print("leaving channel")
                        else:
                            sl_print("failed to leave channel")
                    # /c - get current channel
                    if cmd[0] == '/c':
                        channelname = slack_channelid_to_channelname(current_channel)
                        if channelname is None:
                            sl_print("not in a channel.")
                        else:
                            sl_print(channelname)
                    # /w - list members in current channel
                    if cmd[0] == '/w':
                        if len(cmd) > 1:
                            who_channel = slack_channelname_to_channelid(cmd[1].lower())
                        else:
                            if current_channel is None:
                                sl_print("not in a channel")
                                continue
                            who_channel = current_channel
                        try:
                            channel_name = slack_channelid_to_channelname(who_channel)
                            print "/w in ", channel_name
                            names = []
                            for m in sc.api_call('conversations.members', channel=who_channel)['members']:
                                if slack_get_presence(m):
                                    names.append('!'+slack_userid_to_username(m))
                                else:
                                    names.append(slack_userid_to_username(m))
                            # names = [slack_userid_to_username(m) for m in sc.api_call('conversations.members', channel=who_channel)['members']]
                            print "names:", names
                            sl_print("channel: %s\r\nusers: %s" % (channel_name, ' '.join(names)))
                        except:
                            sl_print("something broke listing users.")
                            
                    # /channels - list channels i'm subscribed to
                    if cmd[0] == '/channels':
                        try:
                            my_channels = [i['name'] for i in sc.api_call('channels.list', exclude_members=True)['channels'] if i['is_member'] is True]
                        except:
                            my_channels = ["can't get list of channels"]
                        sl_print("subscribed channels:\r\n%s" % (' '.join(my_channels)))
        # poll slack for events, which come as a list, always?/usually of only one element.
        for r in sc.rtm_read():
            process_slack_event(r)

else:
    print "Connection failed."
