#! /bin/sh
# Convenience wrapper to invoke the python weather API lookup. 
# Put your zip code in here if you want to have it be the default when
# none is provided from the command line. 
# This is meant to be invoked from a command definition in ser.py, 
# it outputs via stdout. 

if [ -z "$1" ]; then
	ZIP=MY_ZIPCODE
else
	ZIP=$1
fi
cd /opt/ttycommands/weather
./getweather.py -z $ZIP | fmt -s -w 68
