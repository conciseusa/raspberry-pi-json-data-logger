#!/bin/bash
# sudo crontab -e  /  @daily - Run once a day, "0 0 * * *"

DATE=`date +%Y-%m-%d:%H:%M:%S`
cmdf="http://server.com/cmd.json"
echo "$DATE - cmdf = $cmdf"

reset=`curl -s $cmdf | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["'reset'"]'`;
echo "$DATE - reset = $reset"
if [ $reset = "T" ]; then
   echo "$DATE - reboot"
   /sbin/reboot
fi
