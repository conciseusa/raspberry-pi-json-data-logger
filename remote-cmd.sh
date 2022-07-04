#!/bin/bash
# a simple script that can phone home to retrieve information or trigger a command run
# tested on a Raspberry Pi 2022, other platforms, other versions of RPi OS may require fixes running in a crontab
# add cron job running as root to enable reboot feature: sudo crontab -e  /  @daily - Run once a day, "0 0 * * *" / @hourly  0 * * * *
# @daily /home/pi/Work/git/raspberry-pi-json-data-logger/remote-cmd.sh
# set the url where the command file can be controlled, see remote-cmd-config.sh or CMDF below

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
echo "$DATE - $SCRIPT_DIR - $0" >> /tmp/remote-cmd.log # for troubleshooting in cron jobs
echo "$DATE - CMDF = $CMDF" >> /tmp/remote-cmd.log

# to remote trigger a git pull, cmd file = {"reboot":"F", "pull":"T", "data":"Test Data"}
# pull before reboot so updated code will run on reboot
pull=`curl -s $CMDF | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'pull'"]'`;
echo "$DATE - pull = $pull"
if [ $pull = "T" ]; then
   echo "$DATE - pull" >> /tmp/remote-cmd.log
   git -C $SCRIPT_DIR pull >> /tmp/remote-cmd.log
fi

# to remote trigger a reboot, cmd file = {"reboot":"T", "pull":"F", "data":"Test Data"}
# example/testing hosted file with reboot True - https://conciseusa.github.io/remote-cmd-rebootT.json
reboot=`curl -s $CMDF | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'reboot'"]'`;
echo "$DATE - reboot = $reboot"
if [ $reboot = "T" ]; then
   echo "$DATE - reboot" >> /tmp/remote-cmd.log
   /sbin/reboot
fi

# to set a file from remote source, cmd file = {"reboot":"F", "pull":"F", "data":"Test Data"}
# example/testing hosted file with reboot False - https://conciseusa.github.io/remote-cmd-rebootF.json
if [ 0 = 1 ]; then # disable until needed
   data=`curl -s $CMDF | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'data'"]'`;
   echo "$DATE - data = $data"
   echo "$DATE - data = $data" >> /tmp/remote-cmd.log
   echo "$data" > /tmp/remote-cmd.txt
fi
