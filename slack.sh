#! /bin/bash
if [ -z $1 ]; then
	ROOM=teletypes
else
	ROOM=`echo $1 | tr A-Z a-z`
fi

echo "Args: $*" > /tmp/slack.log
echo "1 = $1" >> /tmp/slack.log
echo "ROOM = $ROOM" >> /tmp/slack.log

# It is very important to both nohup and redirect all fd's when starting
# this in the background because otherwise ser.py will wait on it until
# the exec timeout and then kill the whole pgrp. 

nohup python /opt/ttycommands/slack_rtm.py $ROOM  < /dev/null >> /tmp/slack.log 2>&1 &


echo "slack exited"
exit
