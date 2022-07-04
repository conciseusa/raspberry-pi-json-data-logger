#!/usr/bin/python
# get lines of text from serial port, save them to a file
# http://askubuntu.com/questions/715379/how-to-save-gtkterm-output-into-file-automatically

# Permission denied: '/dev/ttyS0'
# Fix: sudo chmod 666 /dev/ttyS0   after every boot
# can also try(better if works):
# sudo adduser <username> dialout # logout / login to have this take effect
# Additional serial port info in Raspberry-Pi-serial-port-cheatsheet.txt

# See serial_log.ini for settings that can be made without changing code

# To start and see errors:
# python3 serial_log.py
# to auto restart use auto-restart.sh, read comments in auto-restart.sh
# Create dir /home/pi/log/ if not aready done. Dirs used on Raspberry Pi, adj as needed.

# If ImportError: No module named serial
# sudo apt-get install python3-serial

from __future__ import print_function
import serial
import io
import sys
if sys.version_info.major != 3:
    sys.exit('Python3 required -> python3 serial_log.py')
import json
import os
from pathlib import Path
import subprocess
import datetime
import time
# from pprint import pprint
import requests
# if not built in, try: sudo apt-get install python-pip ; pip install requests
# or on the RPi: pip install requests
# https://www.raspberrypi.org/documentation/linux/software/python.md
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0


config = ConfigParser()
try:  # first look in shared config dir, then look in same dir as this file
    config.read('../config/serial_log.ini')
except Exception as e:  # catch *all* exceptions in Py3
    print('Exception reading ../config/serial_log.ini: ', str(e))
    sys.exit('Abort - Errors in serial_log.ini')

if 'config' not in config.sections():
    print('serial_log.ini not found in shared config dir: ../config/serial_log.ini')
    try:
        config.read('serial_log.ini')
    except Exception as e:  # catch *all* exceptions in Py3
        print('Exception reading serial_log.ini: ', str(e))
        sys.exit('Abort - Errors in serial_log.ini')
    else:
        print('Warning - It is recommended to copy serial_log.ini to: ../config/serial_log.ini')
        print('    to reduce conflicts pulling updates.'+"\n")

if 'config' not in config.sections():
    print('serial_log.ini not found in current dir')
    sys.exit('Abort - Can not locate serial_log.ini')

if config.has_option('config', 'debugMsg'):
    debugMsg = config.get('config', 'debugMsg')
else:
    debugMsg = False

if config.has_option('config', 'localLog'):
    localLog = config.get('config', 'localLog')
else:
    localLog = 'D'

if config.has_option('config', 'serialp'):
    serialp = config.get('config', 'serialp')
else:
    serialp = '/dev/ttyS0'  # Ubuntu on box with built-in serial port

baud = 9600  # baud rate for serial port

if config.has_option('config', 'url'):  # to send to remote server
    url = config.get('config', 'url')
else:  # turn off send to remote server
    url = ''

if config.has_option('config', 'upkey'):
    upkey = config.get('config', 'upkey')
else:
    upkey = ''

if config.has_option('config', 'url2'):  # to send to remote server 2
    url2 = config.get('config', 'url2')
else:  # turn off send to remote server 2
    url2 = ''

if config.has_option('config', 'upkey2'):
    upkey2 = config.get('config', 'upkey2')
else:
    upkey2 = ''

if config.has_option('config', 'stationId'):
    stationId = config.get('config', 'stationId')
    if not stationId.isalnum():
        sys.exit('Abort - serial_log.ini/stationId use only letters & numbers')
else:
    stationId = '{SerialNumber}'  # get SerialNumber from incomming data

if config.has_option('config', 'hbInterval'):
    hbInterval = config.get('config', 'hbInterval')
else:
    hbInterval = '10M'

if config.has_option('config', 'rmTrigger'):
    # the D or A input that triggers rapid messages (send data on every incomming message)
    rmTrigger = config.get('config', 'rmTrigger')
else:
    rmTrigger = ''

if config.has_option('config', 'rmState'):
    # comparing to a D or A input to trigger rapid message, so convert to int
    rmState = int(config.get('config', 'rmState'))
else:
    rmState = 0  # default to active low

if config.has_option('config', 'signal_labels'):
    signal_labels = dict(item.split(":") for item in
                         config.get('config', 'signal_labels').split('\n'))
else:
    signal_labels = {}

# set log/data file location

if os.path.exists(str(Path.home())+'/log'):
    floc = str(Path.home())+'/log/'  
else:
    floc = str(Path.home())+'/'
fmode = 'a'  # log file mode = append

if stationId != '{SerialNumber}':  # send startup message if sId known, if not known, need to wait for data
    payload = {'type': 'ST'}
    payload['message'] = 'Startup - ' + str(datetime.datetime.now()) + ' Version: 4'
    #! add logic to get ser num, -> do not have a meesage at this point to get ser num
    payload['stationId'] = stationId
    if url:
        if upkey:
            payload['upkey'] = upkey
        try:
            r = requests.post(url, data=payload)
            # auth=('userid', 'password'), if you need it
            print('Startup message: '+r.text)
        except requests.exceptions.RequestException as e:
            print("Startup error: "+str(e)+"\n")
            with open(floc+'error.log', fmode) as errorf:
                errorf.write(str(datetime.datetime.now()) +
                             " - Startup error: " +
                             str(e)+"\n")
                errorf.flush()
    if url2:
        if upkey2:
            payload['upkey'] = upkey2
        else:
            payload.pop('upkey') # incase was set above
        try:
            r = requests.post(url2, data=payload)
            print('Startup message url2: '+r.text)
        except requests.exceptions.RequestException as e:
            print("Startup error url2: "+str(e)+"\n")
            with open(floc+'error.log', fmode) as errorf:
                errorf.write(str(datetime.datetime.now()) +
                             " - Startup error url2: " +
                             str(e)+"\n")
                errorf.flush()

with serial.Serial(serialp, baud) as pt:
    spb = io.TextIOWrapper(io.BufferedRWPair(pt, pt, 1), encoding='ascii',
                           errors='ignore', newline='\n', line_buffering=True)
    # disabled buffering on Armbian Pine A64
    # https://stackoverflow.com/questions/10222788/line-buffered-serial-input
    spb._CHUNK_SIZE = 1
    serial_line = spb.readline()  # read one line of text from serial port
    # throw away first line; might start mid-sentence (incomplete)
    print('1st line serial data ignored.')
    if debugMsg:
        print('1st line serial data: ', serial_line)
    print('', flush=True)  # blank line to make easier to read
    rmPrevData = None # rapid messages - load from rmTrigger, compare with current to sse change
    check_date = None
    hbTime = None

    high_low_tracking = []
    high_values = {}
    low_values = {}
    if config.has_option('config', 'high_low_tracking'):
        high_low_tracking = \
            config.get('config', 'high_low_tracking').split(',')
        for i in high_low_tracking:
            high_values[i] = {}
            high_values[i][i] = 0
            low_values[i] = {}
            low_values[i][i] = 100000  # higher then 16 bit a/d

    if debugMsg:
        print('signal_labels: ', signal_labels)
    remote_watch = {}
    log_time = datetime.datetime.now()

    while (1):
        serial_line = spb.readline()  # read one line of text from serial port
        datetimeStr = str(datetime.datetime.now())
        try:
            parsed_json = json.loads(serial_line)
        except Exception as e:  # catch *all* exceptions in Py3
            print('Bad JSON. Skipping. ', str(e))
            print('', flush=True)  # blank line to make easier to read
            with open(floc+'error.log', fmode) as errorf:
                errorf.write(datetimeStr +
                             " - Bad JSON. Skipping. "+str(e)+"\n")
                errorf.flush()
            continue

        nowTime = datetime.datetime.now()
        if localLog == 'N':
            log_time = None
        if localLog == 'D':
            if log_time.strftime('%d') != nowTime.strftime('%d'):
                log_time = datetime.datetime.now()
        if localLog == 'M':
            if log_time.strftime('%m') != nowTime.strftime('%m'):
                log_time = datetime.datetime.now()
        if localLog == 'Y':
            if log_time.strftime('%y') != nowTime.strftime('%y'):
                log_time = datetime.datetime.now()
        if debugMsg:
            print('Log rotate - nowTime: ', str(nowTime), ', log_time: ', str(log_time))

        if debugMsg:  # echo line of text on-screen
            print(parsed_json)
        #! If time missing, just use time in this script?
        if 'Time' not in parsed_json:  # we should always have Timestamp
            print('Data packet missing Time', flush=True)
            continue  # if not a data logger packet, skip the rest
        print('Serial Data Time: ', parsed_json['Time'], end='\n')
        dtime = time.strptime(parsed_json['Time'], "%Y-%m-%dT%H:%M:%S")
        curr_date = str(dtime.tm_year)
        curr_date += '-'+str(dtime.tm_mon)
        curr_date += '-'+str(dtime.tm_mday)
        curr_hour = str(dtime.tm_hour)
        curr_minute = str(dtime.tm_min)

        # should always have at least one channel of a/d
        if 'A0' not in parsed_json:
            print('Data packet missing A0', flush=True)
            continue  # if not a data logger packet, skip the rest

        for i in high_low_tracking:
            if i in parsed_json:
                label = signal_labels[i] + ':' if i in signal_labels else ''
                # record all data so can see conditions at time of high, low
                if float(parsed_json[i]) > float(high_values[i][i]):
                    high_values[i] = parsed_json.copy()
                    print('New Hi: '+str(high_values[i][i]))
                if float(parsed_json[i]) < float(low_values[i][i]):
                    low_values[i] = parsed_json.copy()
                    print('New Low: '+str(low_values[i][i]))
                if debugMsg:
                    print(label + str(i)+' Hi/Low: '+str(high_values[i][i]) +
                          ' / '+str(low_values[i][i]))
            else:
                print(label + str(i)+' Hi/Low: Value missing.')

        if log_time is not None:
            fileName = floc+str(log_time.strftime('%Y-%m-%d'))+'-serial.log'
            with open(fileName, fmode) as logf:
                logf.write(serial_line)  # write incomming data to file
                logf.flush()  # make sure it actually gets written out

            fileName = floc+str(log_time.strftime('%Y-%m-%d'))+'-data.csv'
            if not os.path.exists(fileName):  # write labels to first line
                with open(fileName, fmode) as logf:
                    delimiter = ''
                    for i in parsed_json.keys():
                        logf.write(delimiter+'"'+str(i)+'"')
                        delimiter = ','
                    logf.write("\n")
                    logf.flush()

            with open(fileName, fmode) as logf:
                delimiter = ''
                for i in parsed_json:
                    logf.write(delimiter+'"'+str(parsed_json[i])+'"')
                    delimiter = ','
                logf.write("\n")
                logf.flush()

        if rmTrigger and (url or url2): # send rapid messages if trigger active
            rmTriggerInt = int(parsed_json[rmTrigger])
            #print('rmState  ', type(rmState))
            if (rmTriggerInt and rmState) or (not rmTriggerInt and not rmState):
                payload = parsed_json
                payload['type'] = 'RM'
                #! add logic to get ser num
                payload['stationId'] = stationId
                
                if url:
                    if upkey:
                        payload['upkey'] = upkey
                    try:
                        r = requests.post(url, data=payload)
                        # auth=('userid', 'password'), if you need it
                        print('Rapid message response: '+r.text)
                    except requests.exceptions.RequestException as e:
                        msgEnd = "Rapid message send error: "+str(e)+"\n"
                        print(msgEnd)
                        with open(floc+'error.log', fmode) as errorf:
                            errorf.write(datetimeStr+" - "+msgEnd)
                            errorf.flush()

                if url2:
                    if upkey2:
                        payload['upkey'] = upkey2
                    try:
                        r = requests.post(url2, data=payload)
                        # auth=('userid', 'password'), if you need it
                        print('Rapid message url2 response: '+r.text)
                    except requests.exceptions.RequestException as e:
                        msgEnd = "Rapid message send url2 error: "+str(e)+"\n"
                        print(msgEnd)
                        with open(floc+'error.log', fmode) as errorf:
                            errorf.write(datetimeStr+" - "+msgEnd)
                            errorf.flush()

        if rmTrigger and parsed_json[rmTrigger] != rmPrevData:  # if signal changed
            if rmPrevData is not None: # skip until rmPrevData set
                remote_watch[str(parsed_json['Time'])] = parsed_json[rmTrigger]
                with open(floc+curr_date+'-serial-summary.log', fmode) as outf:
                    outf.write('rmTrigger:'+str(parsed_json[rmTrigger]))
                    # out full JSON to get timestamp and all conditions
                    outf.write(serial_line)
                    outf.flush()
            rmPrevData = parsed_json[rmTrigger]
            if len(remote_watch):
                print('remote_watch data:')
                for key in sorted(remote_watch):
                    print(key, rmTrigger, remote_watch[key])

        if (curr_date != check_date):  # or (parsed_json['D4']==0) # uncomment for testing
            if (check_date is not None):  # if None, will be set below for next cycle

                # check if disk if filling up
                if os.name == 'nt':
                    dfMsg = 'No disk fill check on Windows'
                else:
                    proc = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
                    output, error = proc.communicate()
                    dfMsg = str(output.strip().decode('ascii'))

                summaryLog = floc+check_date+'-serial-summary.log'
                with open(summaryLog, fmode) as outf:
                    # high/low track same signals, so loop on high to get both
                    for key, high_value in high_values.items():
                        print(str(key)+' high: '+str(high_value[key]),
                              ' low: '+str(low_values[key][key]), file=outf)
                    cmd_out = {"DiskSpace": {"Time": datetimeStr, "df": dfMsg}}
                    print(json.dumps(cmd_out)+"\n", file=outf)
                    outf.flush()
                    sys.stdout.flush()

                # open summary to send, recommended files opened in binary mode
                with open(summaryLog, 'rb') as datafile:
                    # http://stackoverflow.com/questions/16145116/python-requests-post-data-from-a-file
                    payload = {'data': datafile.read()}
                    #payload = datafile.read()
                    device = 'Unknown'  # try to send some device info for remote users
                    if os.path.exists('/proc/device-tree/model'):
                        with open('/proc/device-tree/model') as f:
                            device = f.readlines()
                    elif os.path.exists('/proc/cpuinfo'):
                        with open('/proc/cpuinfo') as f:
                            device = f.readlines()
                    payload['device'] = device
                    payload['type'] = 'SR'
                    #! add logic to get ser num
                    payload['stationId'] = stationId
                    if upkey:
                        payload['upkey'] = upkey
                    # headers={'content-type':'application/x-www-form-urlencoded'}
                    # , headers=headers
                    if url:
                        if upkey:
                            payload['upkey'] = upkey
                        try:
                            r = requests.post(url, data=payload)
                            # auth=('userid', 'password'), if you need it
                            print('Summary upload: '+r.text)
                        except requests.exceptions.RequestException as e:
                            msgEnd = "Summary upload error: "+str(e)+"\n"
                            print(msgEnd)
                            with open(floc+'error.log', fmode) as errorf:
                                errorf.write(datetimeStr + " - " + msgEnd)
                                errorf.flush()

                    if url2:
                        if upkey2:
                            payload['upkey'] = upkey2
                        try:
                            r = requests.post(url2, data=payload)
                            # auth=('userid', 'password'), if you need it
                            print('Summary upload url2: '+r.text)
                        except requests.exceptions.RequestException as e:
                            msgEnd = "Summary upload url2 error: "+str(e)+"\n"
                            print(msgEnd)
                            with open(floc+'error.log', fmode) as errorf:
                                errorf.write(datetimeStr + " - " + msgEnd)
                                errorf.flush()

                # reset trackers
                for i in high_low_tracking:
                    high_values[i] = {}
                    high_values[i][i] = 0
                    low_values[i] = {}
                    low_values[i][i] = 100000  # higher then 16 bit a/d

                remote_watch.clear()
            check_date = curr_date

        # send heartbeat message
        if debugMsg:
            print('Check heartbeat time: ', hbInterval, '/', hbTime, end='\n')
        message = ''
        messagefile = None
        try:
            messagefile = open('../config/message.txt', 'r', encoding='utf-8')
        except OSError:
            print("No message.txt file")
        # no code here, exceptions will not close the file
        if messagefile:
            with messagefile:
                # only for sending short messages
                message = messagefile.read(2100)
                if len(message) > 2000:
                    print("Oversized message.txt file. 2000 max. Size: ",
                          len(message))
        # or (parsed_json['D8'] == 0 to trigger faster then 1 min when testing
        if (hbTime is not None):
            if ((hbInterval == 'H' and curr_hour != hbTime) or
                (hbInterval == '10M' and int(int(curr_minute) / 10) != hbTime)
                    or (hbInterval == 'M' and curr_minute != hbTime)):

                payload = parsed_json
                payload['type'] = 'HB'
                #! add logic to get ser num
                payload['stationId'] = stationId

                if message:
                    payload['message'] = message

                if url:
                    if upkey:
                        payload['upkey'] = upkey
                    try:
                        r = requests.post(url, data=payload)
                        # auth=('userid', 'password'), if you need it
                        print(datetimeStr + ' - Heartbeat message: '+r.text)
                    except requests.exceptions.RequestException as e:
                        msgEnd = str(e)+"\n"
                        print("Heartbeat message send error: "+msgEnd)
                        with open(floc+'error.log', fmode) as errorf:
                            errorf.write(datetimeStr +
                                         " - Heartbeat send error: "+msgEnd)
                            errorf.flush()
                if url2:
                    if upkey2:
                        payload['upkey'] = upkey2
                    try:
                        r = requests.post(url2, data=payload)
                        # auth=('userid', 'password'), if you need it
                        print(datetimeStr + ' - Heartbeat message url2: '+r.text)
                    except requests.exceptions.RequestException as e:
                        msgEnd = str(e)+"\n"
                        print("Heartbeat message url2 send error: "+msgEnd)
                        with open(floc+'error.log', fmode) as errorf:
                            errorf.write(datetimeStr +
                                         " - Heartbeat send url2 error: "+msgEnd)
                            errorf.flush()
                if (hbInterval == 'H'):
                    hbTime = curr_hour
                if (hbInterval == '10M'):
                    hbTime = int(int(curr_minute) / 10)
                if (hbInterval == 'M'):
                    hbTime = curr_minute
        else:  # seed hbTime
            if (hbInterval == 'H'):
                hbTime = curr_hour
            if (hbInterval == '10M'):
                hbTime = int(int(curr_minute) / 10)
            if (hbInterval == 'M'):
                hbTime = curr_minute

        # shows how to delete files
        # look into auto delete of old log files so disk does not fill up
        # https://www.tutorialspoint.com/python3/python_files_io.htm
        print('', flush=True)  # blank line to make easier to read
