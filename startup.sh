#! /bin/sh

# This is a convenience script to start all the components of the
# teletype interface software. Just run this once at system startup. 

mkdir -p /var/spool/tty
chmod 777 /var/spool/tty
killall inoticoming || //bin/true

# Start the main process that manages the tty loop serial link, ser.py
start-in-screen -t ser.py /opt/ttycommands/ser.py

# Start the queue processor that prints files to the tty loop on demand.
inoticoming --initialsearch /var/spool/tty  /opt/ttycommands/process-incoming.sh {} \;

# Start the HTTP CGI server to receive API calls from SMS/voicemail providers,
# if set up. 
start-in-screen -t cgiserver /opt/ttycommands/serve-cgi.sh

# If you have an email account set up for realtime inbound email, this will
# start the email client for it. (see README)
su teletype -c fetchmail

