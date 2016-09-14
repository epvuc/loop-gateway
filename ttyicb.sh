#! /bin/sh
# Convenience wrapper to invoke the ttyicb program safely. 
echo "starting icb"
nohup /opt/ttycommands/ttyicb < /dev/null > /dev/null 2>&1 &
