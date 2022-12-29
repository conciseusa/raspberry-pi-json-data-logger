#!/bin/bash

# script to help setup raspberry-pi-json-data-logger
# run this script in the dir where the raspberry-pi-json-data-logger clone dir should created
# or run some or all the commands one by one on the command line
# this script assumes one checkout of raspberry-pi-json-data-logger running with one serial port

# raspberry-pi-json-data-logger looks for a log dir in the home dir to write log files to
mkdir -p $HOME/log

# raspberry-pi-json-data-logger looks for a config dir in its parent dir for configuration info
mkdir -p config

# this script assumes git is already installed and there is an Internet connection to clone files
echo "clone raspberry-pi-json-data-logger"
git clone https://github.com/conciseusa/raspberry-pi-json-data-logger.git

# copy default ini file to config dir so updates will not conflict with upstream changes
# review config/serial_log.ini and make any needed changes
# backup file if already present
[ -f config/serial_log.ini ] && mv config/serial_log.ini config/serial_log_$(date +%T).ini
cp raspberry-pi-json-data-logger/serial_log.ini config/serial_log.ini

# add auto start on reboot, comment out code below to not auto start
# if auto start does not seem to be working,
# it can be useful to run python3 serial_log.py in the terminal where you can see error messages
COMMAND="@reboot $(pwd)/raspberry-pi-json-data-logger/auto-restart.sh"
echo "Add $COMMAND to crontab"
if crontab -l | grep -q 'raspberry-pi-json-data-logger/auto-restart.sh'; then
  echo "auto-restart.sh already exists in crontab"
else
  (crontab -l 2>/dev/null || true; echo "$COMMAND") | crontab -
  # config needed for auto start
  touch config/cron-config.sh
  echo "LOG_DIR=$HOME/log" > config/cron-config.sh
  echo "SCRIPT_DIR=$(pwd)/raspberry-pi-json-data-logger" >> config/cron-config.sh
fi

echo "Setup script finished"

# serve this file from a local web server to make it easy to load on devices without a gui
# sudo cp setup.sh /var/www/html/setup.sh # copy on server example
# wget 192.168.1.173/setup.sh # get on target device example
# sh setup.sh # run on target

# test that logger can start up and connecto to serial port:
# cd raspberry-pi-json-data-logger
# python3 serial_log.py
# Fixes for some common errors:
# ImportError: No module named serial
# sudo pip3 install pyserial
# ImportError: No module named requests
# sudo pip3 install requests
# For serial error: could not open port *** Permission denied
# Adding your user to the dialout group will typically fix the issue.
# sudo adduser YourUserName dialout
# logout and login

# this setup file focuses on getting the main py data logging script up and running
# see the readme and ini files for other options/features:
# Jupyter Notebook data loading, offsite data storage, setpoint control, remote restart, etc.
