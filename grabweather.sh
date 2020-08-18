#! /bin/sh
if [ -z "$1" ]; then
	ZIP=94117
else
	ZIP=$1
fi
cd /opt/ttycommands/weather
./getweather.py -z $ZIP | sed 's/\%/ percent/' | fmt -s -w 68
