#! /bin/bash
if [ -z $1 ]; then
	JID='TARGET_XMPPUSER'
else
	JID=$1
fi

nohup /opt/ttycommands/new-xtty.py $JID < /dev/null > /var/log/xtty.log 2>&1 &
