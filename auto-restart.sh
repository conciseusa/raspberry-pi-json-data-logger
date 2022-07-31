#!/bin/bash
# Walter Spurgiasz 2022
# Add to crontab (@reboot /home/pi/Work/git/raspberry-pi-json-data-logger/auto-restart.sh) so at restart :
# wait for network to come up and auto restart serial_log.py at reboot and on error (checkout in ~/Work/git/raspberry-pi-json-data-logger):
# Create log dir ~/log/ if not aready done. Dirs used on Raspberry Pi, adj as needed.
# cron-config.sh needs full paths for running from crontab
# Ctrl-z should exit loop (may take a number of trys)

DATE=`date +%Y-%m-%d:%H:%M:%S`
SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
source $SCRIPT_DIR/../config/cron-config.sh # hardcode to config dir if needed

# sometimes @reboot will start before the network is online, so wait until network is up
until ping -c 1 -W 1 8.8.8.8; do sleep 1; done;
# cd to the dir with the script to run
cd $SCRIPT_DIR;
echo "$DATE - First start serial_log" >> $LOG_DIR/serial_log_restart.log;
# start script in an endless while loop so restarts on an error
while true; do python3 serial_log.py; DATE=`date +%Y-%m-%d:%H:%M:%S`; echo "$DATE - Restarting serial_log" >> $LOG_DIR/serial_log_restart.log; test $? -gt 128 && break; sleep 10; done;
