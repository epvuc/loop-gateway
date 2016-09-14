#! /bin/sh

mkdir -p /var/spool/tty
chmod 777 /var/spool/tty
killall inoticoming || //bin/true

/opt/ttycommands/start-in-screen -t ser.py /opt/ttycommands/ser.py

inoticoming --initialsearch /var/spool/tty  /opt/ttycommands/process-incoming.sh {} \;

/opt/ttycommands/start-in-screen -t cgiserver /opt/ttycommands/serve-cgi.sh

su teletype -c fetchmail

