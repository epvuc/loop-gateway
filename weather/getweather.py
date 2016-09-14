#! /usr/bin/python
from nwsweatherreport import getnwsforecast, getplacelatlong, getziplatlong
from optparse import OptionParser
import sys

usage = "getweather.py -z <zipcode>"
parser = OptionParser(usage)
parser.add_option("-z", "--zip", action="store", type="string", dest="zip")
(options, args)=parser.parse_args()
print "ZCZC WEATHER"
if not options.zip: 
	parser.error("ZIP code is required")

(msg,lat,lon)=getziplatlong(options.zip, False)
if msg: 
	print("Error: "+msg)
else: 
	s=getnwsforecast(float(lat),float(lon),False)
	print s
print "NNNN"
