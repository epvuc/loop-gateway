#! /bin/sh
echo ""
echo "ZCZC AP NEWS" `date +"%b %d %Y"`

if [ "$1" = "long" ] || [ "$1" = "LONG" ]; then
	rsstail  -d -H  -1  -u "http://hosted.ap.org/lineups/WORLDHEADS-rss_2.0.xml?SITE=KYB66&SECTION=HOME"  | sed 's/^Title: /\n- /;s/^Description: //;s/\.\.\.$//' | fmt -s -w 68
else
	rsstail  -N  -1  -u "http://hosted.ap.org/lineups/WORLDHEADS-rss_2.0.xml?SITE=KYB66&SECTION=HOME" | sed 's/^ //' | fmt -s -w 68 | perl -lne 'print "$_\r\n";'
fi

echo "NNNN"
