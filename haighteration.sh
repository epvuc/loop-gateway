#! /bin/sh
echo "ZCZC HAIGHTERATION" `date +"%b %d %Y"`

if [ "$1" = "long" ] || [ "$1" = "LONG" ]; then
	# long
	rsstail  -d -H  -1  -u "http://hoodline.com/atom/lower-haight" > /tmp/feed.$$
	sed 's/&#8217;/'\''/g' /tmp/feed.$$ > /tmp/recode.$$
	recode -f HTML..ASCII /tmp/recode.$$
	sed 's/Title: /\n- /;s/^Description: //;s/Continue reading/.../' /tmp/recode.$$ | fmt -s -w 68
	rm /tmp/feed.$$ /tmp/recode.$$
else
	# short
	rsstail  -N  -1  -u "http://hoodline.com/atom/lower-haight"  > /tmp/feed.$$
	sed 's/&#8217;/'\''/g' /tmp/feed.$$ > /tmp/recode.$$
	recode -f HTML..ASCII /tmp/recode.$$
	sed 's/^ //' /tmp/recode.$$ | fmt -s -w 68
	rm /tmp/feed.$$ /tmp/recode.$$
fi
echo "NNNN"
