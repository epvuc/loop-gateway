#! /bin/bash
# Convenience wrapper to invoke slack.py Slack client with the correct
# command line parameters.  See slack.py for details of how to log in to
# Slack using the XMPP interface, then fill in the details here, and call
# this program from ser.py as a command. 

if [ -z $1 ]; then
	ROOM=teletypes
else
	ROOM=`echo $1 | tr A-Z a-z`
fi

echo "starting Slack."
sleep 1

echo "Args: $*" > /tmp/slack.log
echo "1 = $1" >> /tmp/slack.log
echo "ROOM = $ROOM" >> /tmp/slack.log

# It is very important to both nohup and redirect all fd's when starting
# this in the background because otherwise ser.py will wait on it until
# the exec timeout and then kill the whole pgrp. 

nohup python /opt/ttycommands/new-slack.py -j MY_SLACK_USERNAME@MY_SLACK_TEAM.xmpp.slack.com -p MY_SLACK_TEAM.MY_SLACK_PASSWORD -r ${ROOM}@conference.MY_SLACK_TEAM.xmpp.slack.com -n MY_SLACK_USERNAME < /dev/null > /dev/null 2>&1 &


exit
