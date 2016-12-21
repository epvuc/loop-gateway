#! /bin/sh

/opt/ttycommands/new-telestream.py $* < /dev/null >> /tmp/telestream.log 2>&1 &
