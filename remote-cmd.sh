#!/bin/bash
# a simple script that can phone home to retrieve information or trigger a command run
# to add cron job:
# sudo crontab -e  /  @daily - Run once a day, "0 0 * * *" / @hourly  0 * * * *
# Raspberry Pi
# @daily /home/pi/Work/git/raspberry-pi-json-data-logger/remote-cmd.sh

DATE=`date +%Y-%m-%d:%H:%M:%S`
SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
# add full cmd paths (/usr/bin/ most Linux) if no path set:
# SCRIPT_DIR=$(/usr/bin/dirname $(/usr/bin/readlink -f "$BASH_SOURCE"))
# more info:
# https://stackoverflow.com/questions/59895/how-can-i-get-the-directory-where-a-bash-script-is-located-from-within-the-scrip

# CMDF="http://server.com/cmd.json" # to set the cmd url here, uncomment this line, comment out source command
# or better to keep config seperate in a config dir in the parent dir
# source below has worked in testing, but may need to hardcode path in some situations
source $SCRIPT_DIR/../config/remote-cmd-config.sh
echo "$DATE - CMDF = $CMDF"
echo "$DATE - $SCRIPT_DIR - $0" >> /tmp/remote-data.log # for troubleshooting in cron jobs
echo "$DATE - CMDF = $CMDF" >> /tmp/remote-data.log

# to remote trigger a reset, cmd file = {"reset":"T", "data":"Test Data"}
# example/testing hosted file with reset True - https://conciseusa.github.io/remote-cmd-resetT.json
reset=`curl -s $CMDF | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'reset'"]'`;
echo "$DATE - reset = $reset"
if [ $reset = "T" ]; then
   echo "$DATE - reboot"
   /sbin/reboot
fi

# to set a file from remote source, cmd file = {"reset":"T", "data":"Test Data"}
# example/testing hosted file with reset False - https://conciseusa.github.io/remote-cmd-resetF.json
data=`curl -s $CMDF | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'data'"]'`;
echo "$DATE - data = $data"
echo "$data" > /tmp/remote-data.txt
