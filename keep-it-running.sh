#! /bin/sh
# This is just a safety to restart ser.py if it crashes. 
# Probably not needed, but it would be annoying if it died. 
while true;  do
	echo -n "ser.py starting at "
	date
	/opt/ttycommands/ser.py
	sleep 2
done

