#!/usr/bin/python
# get lines of text from serial port, save them to a file
# http://askubuntu.com/questions/715379/how-to-save-gtkterm-output-into-file-automatically

# Permission denied: '/dev/ttyS0'
# Fix: sudo chmod 666 /dev/ttyS0   after every boot
# can also try(better if works): sudo adduser <username> dialout # logout / login to have this take effect

# Handy for watching raw serial data - !! when running screen and this script, it will grab most of the data before this script !!
# sudo apt-get install screen
# screen /dev/ttyS0 9600
# exit Ctrl-a k (release Ctrl-a before pressing k)
# http://www.catonmat.net/blog/screen-terminal-emulator-cheat-sheet/

# python serial_log.py
# while true; do python serial_log.py; echo "serial_log was killed, restarting it"; test $? -gt 128 && break; done
# Ctrl-z should exit loop
# @reboot


from __future__ import print_function
import serial, io
import json, os
import subprocess
import datetime
import time
from pprint import pprint
import requests # not a built in (Ubuntu): sudo apt-get install python-pip ; pip install requests
# or on the RPi: pip install requests - https://www.raspberrypi.org/documentation/linux/software/python.md
try:
   from configparser import ConfigParser
except ImportError:
   from ConfigParser import ConfigParser  # ver. < 3.0

config = ConfigParser()
config.read('serial_log.ini')

if config.has_option('config', 'serialp'):
   serialp = config.get('config', 'serialp')
else:
   #serialp  = '/dev/ttyUSB0'  # serial port to read data from
   serialp  = '/dev/ttyS0'     # Ubuntu on P4 and Atom ITX 2016
   #serialp  = '/dev/ttyS2'     # Pine A64
   #serialp  = '/dev/ttyAMA0'   # Raspberry Pi, need to disable serial login first -> sudo raspi-config
baud  = 9600             # baud rate for serial port

if config.has_option('config', 'url'):
   url = config.get('config', 'url')
else:
   url = 'http://somewhere.com/remote-data.php' # to send to remote server

if config.has_option('config', 'senderid'):
   senderid = config.get('config', 'senderid')
else:
   senderid = 'dev1'

if config.has_option('config', 'upkey'):
   upkey = config.get('config', 'upkey')
else:
   upkey = 'key1'

floc = os.getenv("HOME")+'/'  # log file location
fmode = 'a'  # log file mode = append

# send startup message
payload = {'data': str(datetime.datetime.now())+' Start up Ver: 2', 'type': 'ST', 'upkey': upkey, 'senderid': senderid}
try:
   r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
   print ('Startup message: '+r.text)
except requests.exceptions.RequestException as e:
   print ("Startup error: "+str(e)+"\n")
   with open(floc+'error.log',fmode) as outf:
      outf.write(str(datetime.datetime.now())+" - Startup error: "+str(e)+"\n")
      outf.flush()

with serial.Serial(serialp,baud) as pt, open(floc+str(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))+'-serial.log',fmode) as logf:
   spb = io.TextIOWrapper(io.BufferedRWPair(pt,pt,1), encoding='ascii', errors='ignore', newline='\r',line_buffering=True)
   spb.readline()  # throw away first line; likely to start mid-sentence (incomplete)
   D7 = None
   check_date = None
   check_hour = None
   high_temp = {'A0': 0}
   low_temp = {'A0': 1101}
   high_batt = {'A1': 0}
   low_batt = {'A1': 1102}
   well_run = {}
   while (1):
      x = spb.readline() # read one line of text from serial port
      try:
         parsed_json = json.loads(x)
      except:
         print ('Bad JSON. Skipping.')
         print ('') # blank line to make easier to read
         with open(floc+'error.log',fmode) as outf:
            outf.write(str(datetime.datetime.now())+" - Bad JSON. Skipping.\n")
            outf.flush()
         continue
      print (parsed_json['Time'],end='\n')   #echo line of text on-screen
      print (parsed_json)
      #print (x,end='')   #echo line of text on-screen
      if not 'A0' in parsed_json:
         print ('') # blank line to make easier to read
         continue # if not a data logger packet, skip the rest

      dtime = time.strptime(parsed_json['Time'], "%Y-%m-%dT%H:%M:%S")
      curr_date = str(dtime.tm_year)+'-'+str(dtime.tm_mon)+'-'+str(dtime.tm_mday)
      curr_hour = str(dtime.tm_hour)
      if float(parsed_json['A0']) > float(high_temp['A0']):
         high_temp = parsed_json.copy() # record all data so can see conditions at time of high, low
      if float(parsed_json['A0']) < float(low_temp['A0']):
         low_temp = parsed_json.copy()
      if float(parsed_json['A1']) > float(high_batt['A1']):
         high_batt = parsed_json.copy()
      if float(parsed_json['A1']) < float(low_batt['A1']):
         low_batt = parsed_json.copy()
      print ('Temp: '+str(high_temp['A0'])+', '+str(low_temp['A0']))
      print ('Batt: '+str(high_batt['A1'])+', '+str(low_batt['A1']))
      print ('well_run')
      for key in sorted(well_run):
         print (key, well_run[key])
      print (dtime)
      print ('') # blank line to make easier to read

      logf.write(x)      #write line of text to file
      logf.flush()       #make sure it actually gets written out

      if not parsed_json['D7']: # send well run messages
         payload = {'data': x, 'type': 'WR', 'upkey': upkey, 'senderid': senderid}
         try:
            r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
            print ('Well run message: '+r.text)
         except requests.exceptions.RequestException as e:
            print ("Well run error: "+str(e)+"\n")
            with open(floc+'error.log',fmode) as outf:
               outf.write(str(datetime.datetime.now())+" - Well run error: "+str(e)+"\n")
               outf.flush()

      if parsed_json['D7'] != D7:
         if D7 != None:
            well_run[str(parsed_json['Time'])] = parsed_json['D7']
            with open(floc+curr_date+'-serial-summary.log',fmode) as outf:
               outf.write('D7 -> WR:'+str(parsed_json['D7']))
               outf.write(x) # output full JSON to get a timestamp and all conditions at this moment
               outf.flush()
         D7 = parsed_json['D7']

      if (curr_date != check_date) or (parsed_json['D6'] == 0): # second clause is to trigger when testing
         if (check_date != None):

            # check if disk if filling up
            process = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
            output, error = process.communicate()
            
            # add highs and lows to check (previous) date log in a last write to that file
            with open(floc+check_date+'-serial-summary.log',fmode) as outf:
               print ('A0 -> HT:'+str(high_temp['A0']), high_temp, file=outf)
               print ('A0 -> LT:'+str(low_temp['A0']), low_temp, file=outf)
               print ('A1 -> HB:'+str(high_batt['A1']), high_batt, file=outf)
               print ('A1 -> LB:'+str(low_batt['A1']), low_batt, file=outf)
               print (output.strip(), file=outf)
               print (x.strip()+"\n", file=outf)
               outf.flush()

            with open(floc+check_date+'-serial-summary.log', 'rb') as datafile: # recommended that you open files in binary mode
               # http://stackoverflow.com/questions/16145116/python-requests-post-data-from-a-file
               payload = {'data': datafile.read(), 'type': 'SR', 'upkey': upkey, 'senderid': senderid}
               # headers = {'content-type': 'application/x-www-form-urlencoded'} , headers=headers
               try:
                  r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
                  print ('Summary upload: '+r.text)
               except requests.exceptions.RequestException as e:
                  print ("Summary upload error: "+str(e)+"\n")
                  with open(floc+'error.log',fmode) as outf:
                     outf.write(str(datetime.datetime.now())+" - Summary upload error: "+str(e)+"\n")
                     outf.flush()

            # reset trackers
            low_temp['A0'] = 1111
            high_temp['A0'] = 0.0
            low_batt['A1'] = 1112
            high_batt['A1'] = 0.0
            well_run.clear()
         check_date = curr_date
      
      # send heartbeat message once an hour
      if (curr_hour != check_hour): # or (parsed_json['D6'] == 0): # second clause is to trigger when testing
         if (check_hour != None):
            payload = {'data': x, 'type': 'HB', 'upkey': upkey, 'senderid': senderid}
            try:
               r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
               print ('Heartbeat message: '+r.text)
            except requests.exceptions.RequestException as e:
               print ("Heartbeat message error: "+str(e)+"\n")
               with open(floc+'error.log',fmode) as outf:
                  outf.write(str(datetime.datetime.now())+" - Heartbeat message error: "+str(e)+"\n")
                  outf.flush()
         check_hour = curr_hour
         
