#! /bin/bash

# This is a simple script to dequeue messages from /var/spool/tty and feed them
# to the teletype machine. To use it, have the following command running: 
#
# inoticoming /var/spool/tty /opt/ttycommands/process-incoming.sh {} \;
#
# Whenever a new file appears in /var/spool/tty, inoticoming will execute this
# script with the new file's name as an argument; this script will then feed
# it to the loop via "new-telepipe.py" which handles formatting and power up/down.


echo ""
NAME=$1
echo PROCESSING $NAME

# Test first char of filename to decide which teletype to power on if any
if [[ ${NAME:0:1} == "T" ]] ; then 
  cat /var/spool/tty/$1 | /opt/ttycommands/new-telepipe.py -p
elif [[ ${NAME:0:1} == "R" ]] ; then
  cat /var/spool/tty/$1 | /opt/ttycommands/new-telepipe.py -pr
else
  cat /var/spool/tty/$1 | /opt/ttycommands/new-telepipe.py 
fi

echo REMOVING $1
rm /var/spool/tty/$1
exit 0
