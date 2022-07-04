#!/bin/bash
# Walter Spurgiasz 2022
# Add to crontab so at restart (@reboot /home/pi/Work/git/raspberry-pi-json-data-logger/auto-restart.sh):
# wait for network to come up and auto restart serial_log.py on error (checkout in /home/pi/Work/git/):
# Create dir /home/pi/log/ if not aready done. Dirs used on Raspberry Pi, adj as needed.
# Ctrl-z should exit loop, update serial_log.py to use with other scripts

DATE=`date +%Y-%m-%d:%H:%M:%S`
# sometimes @reboot will start before the network is online, so wait until network is up
until ping -c 1 -W 1 8.8.8.8; do sleep 1; done;
# cd to the dir with the script to run
cd /home/pi/Work/git/raspberry-pi-json-data-logger;
echo "$DATE - First start serial_log" >> /home/pi/log/serial_log_restart.log;
# start script in an endless while loop so restarts on an error
while true; do python3 serial_log.py; echo "$DATE - Restarting serial_log" >> /home/pi/log/serial_log_restart.log; test $? -gt 128 && break; done;
