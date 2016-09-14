#! /bin/sh
cat > /tmp/ttymail.$$
( 
echo ""
echo "zczc email"
grep -a ^From /tmp/ttymail.$$ | head -1 | sed 's/@/ at /'
grep -a ^Subj /tmp/ttymail.$$ | head -1
/opt/ttycommands/mime-extract.py < /tmp/ttymail.$$ | fmt -s -w 72 | head -30
echo nnnn ) | cut -c1-72 | head -34 > /tmp/ttymail2.$$
# rm /tmp/ttymail.$$

LINES=`wc -l /tmp/ttymail2.$$ | awk '{ print $1 }'`
if [ $LINES -lt 4 ]; then
        echo "nothing to print."
        rm -f /tmp/ttymail2.$$
        exit
fi

# send it to the machine

cat /tmp/ttymail2.$$ >> /home/teletype/tty/msglog
cat /tmp/ttymail2.$$ > /var/spool/tty/T`date +%s_%N`
rm -f /tmp/ttymail2.$$

exit 
