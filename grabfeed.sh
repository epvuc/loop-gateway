#! /bin/sh
echo ""
echo "ZCZC AP NEWS" `date +"%b %d %Y"`
echo ""

if [ "$1" = "long" ] || [ "$1" = "LONG" ]; then
	rsstail  -d -H  -1  -u "http://hosted2.ap.org/atom/APDEFAULT/cae69a7523db45408eeb2b3a98c0c9c5"  | sed 's/^Title: /\n- /;s/^Description: //;s/\.\.\.$//' | fmt -s -w 68
else
	rsstail  -N  -1  -u "http://hosted2.ap.org/atom/APDEFAULT/cae69a7523db45408eeb2b3a98c0c9c5" | sed 's/^ //' | fmt -s -w 68 | perl -lne 'print "$_\r\n";'

fi

echo "NNNN"
