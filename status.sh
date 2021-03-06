#! /bin/sh
echo -n "uptime: "
uptime | perl -lne 'print $1 if /up (.*?),/;'
# ip addr 10.0.0.148  metric 202  (10.0.0.0/24, eth0)
ip r | perl -lne 'print "ip addr $3 ($1, $2)" if /^(.*?) dev (.*)  proto kernel  scope link  src (.*?) /;'
#iwconfig wlan0 | grep wlan0
#iwconfig wlan0 | perl -lne 'print "wifi link $1" if /Link Quality=(.*?) /;'
echo -n "screens: "
screen -ls | grep autosession | awk '{ print $1 }' | cut -d. -f2 | fmt
echo -n "ser.py pid: "
pgrep -f "python /opt/ttycommands/ser.py" || echo MISSING
echo -n "rf cmd rcvr: "
pgrep -f mochad-command-runner || echo MISSING
echo -n "ttybot pid: "
pgrep ttybot.py || echo MISSING
echo -n "twitter stream: "
pgrep -f new-telestream.py > /dev/null || echo "Not running." && ps axw | perl -lne 'print $1 if /python .*\/(new-telestream.py .*)/;'
echo -n "xmpp client: "
pgrep xtty.py > /dev/null || echo "Not running." && ps axw | perl -lne 'print $1 if /python \/opt\/ttycommands\/(xtty.py .*)/;'
