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

# ImportError: No module named serial
# sudo apt-get install python3-serial

# python3 serial_log.py
# to auto restart:
# while true; do python3 serial_log.py; echo "serial_log was killed, restarting it"; test $? -gt 128 && break; done
# Ctrl-z should exit loop
# @reboot


from __future__ import print_function
import serial, io, sys
import json, os
import subprocess
import datetime
import time
from pprint import pprint
import requests # if not a built in, try: sudo apt-get install python-pip ; pip install requests
# or on the RPi: pip install requests - https://www.raspberrypi.org/documentation/linux/software/python.md
try:
	from configparser import ConfigParser
except ImportError:
	from ConfigParser import ConfigParser  # ver. < 3.0

config = ConfigParser()
try:  # first look in shared config dir, then look in same dir as this file
	config.read('../../config/serial_log.ini')
except:
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

if config.has_option('config', 'heartbeat_interval'):
	heartbeat_interval = config.get('config', 'heartbeat_interval')
else:
	heartbeat_interval = 'H'

floc = os.getenv("HOME")+'/'  # log file location
fmode = 'a'  # log file mode = append

# send startup message
payload = {'data': '{"Startup":{"Time":"'+str(datetime.datetime.now())+'", "Version":"3"}}', 'type': 'ST', 'upkey': upkey, 'senderid': senderid}
try:
	r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
	print ('Startup message: '+r.text)
except requests.exceptions.RequestException as e:
	print ("Startup error: "+str(e)+"\n")
	with open(floc+'error.log',fmode) as errorf:
		errorf.write(str(datetime.datetime.now())+" - Startup error: "+str(e)+"\n")
		errorf.flush()

with serial.Serial(serialp,baud) as pt:
	spb = io.TextIOWrapper(io.BufferedRWPair(pt,pt,1), encoding='ascii', errors='ignore', newline='\n',line_buffering=True)
	spb._CHUNK_SIZE = 1  # disabled buffering on Armbian Pine A64 - https://stackoverflow.com/questions/10222788/line-buffered-serial-input
	spb.readline()  # throw away first line; likely to start mid-sentence (incomplete)
	D7 = None
	check_date = None
	heartbeat_time = None
	#high_temp = {'A0': 0}
	#low_temp = {'A0': 1101}
	#high_batt = {'A1': 0}
	#low_batt = {'A1': 1102}
	high_low_tracking = []
	high_values = {}
	low_values = {}
	if config.has_option('config', 'high_low_tracking'):
		high_low_tracking = config.get('config', 'high_low_tracking').split(',')
		for i in high_low_tracking:
			high_values[i] = {}
			high_values[i][i] = 0
			low_values[i] = {}
			low_values[i][i] = 100000  # higher then 16 bit a/d
	signal_labels = dict(item.split(":") for item in config.get('config', 'signal_labels').split('\n'))
	print ('signal_labels.', signal_labels)
	remote_watch = {}
	log_time = datetime.datetime.now()

	while (1):
		x = spb.readline() # read one line of text from serial port
		try:
			parsed_json = json.loads(x)
		except:
			print ('Bad JSON. Skipping.')
			print ('', flush=True) # blank line to make easier to read
			with open(floc+'error.log',fmode) as errorf:
				errorf.write(str(datetime.datetime.now())+" - Bad JSON. Skipping.\n")
				errorf.flush()
			continue

		if not 'Time' in parsed_json:  # we should always have Timestamp
			print ('Data packet missing Time', flush=True)
			continue # if not a data logger packet, skip the rest
		dtime = time.strptime(parsed_json['Time'], "%Y-%m-%dT%H:%M:%S")
		curr_date = str(dtime.tm_year)+'-'+str(dtime.tm_mon)+'-'+str(dtime.tm_mday)
		curr_hour = str(dtime.tm_hour)
		curr_minute = str(dtime.tm_min)
		print (parsed_json['Time'],end='\n')  # echo line of text on-screen
		print (parsed_json)
		if not 'A0' in parsed_json:  # we should always have at least one channel of a/d
			print ('Data packet missing A0', flush=True)
			continue # if not a data logger packet, skip the rest

		#if float(parsed_json['A0']) > float(high_temp['A0']):
		#	high_temp = parsed_json.copy() # record all data so can see conditions at time of high, low
		#if float(parsed_json['A0']) < float(low_temp['A0']):
		#	low_temp = parsed_json.copy()
		#if float(parsed_json['A1']) > float(high_batt['A1']):
		#	high_batt = parsed_json.copy()
		#if float(parsed_json['A1']) < float(low_batt['A1']):
		#	low_batt = parsed_json.copy()
		#print ('Temp Hi/Low: '+str(high_temp['A0'])+', '+str(low_temp['A0']))
		#print ('Batt Hi/Low: '+str(high_batt['A1'])+', '+str(low_batt['A1']))
		for i in high_low_tracking:
			if i in parsed_json:
				label = signal_labels[i] + ':' if i in signal_labels else ''
				if float(parsed_json[i]) > float(high_values[i][i]):
					high_values[i] = parsed_json.copy() # record all data so can see conditions at time of high, low
				if float(parsed_json[i]) < float(low_values[i][i]):
					low_values[i] = parsed_json.copy()
				print (label + str(i)+' Hi/Low: '+str(high_values[i][i])+' / '+str(low_values[i][i]))
			else:
				print (label + str(i)+' Hi/Low: Value missing.')

		print ('remote_watch')
		for key in sorted(remote_watch):
			print (key, remote_watch[key])
		print (dtime)
		print ('', flush=True) # blank line to make easier to read

		with open( floc+str(log_time.strftime('%Y-%m-%d_%H:%M:%S'))+'-serial.log',fmode) as logf:
			logf.write(x)      #write line of text to file
			logf.flush()       #make sure it actually gets written out

		if not parsed_json['D7']: # send well run messages
			payload = {'data': x, 'type': 'WR', 'upkey': upkey, 'senderid': senderid}
			try:
				r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
				print ('Well run message: '+r.text)
			except requests.exceptions.RequestException as e:
				print ("Well run send error: "+str(e)+"\n")
				with open(floc+'error.log',fmode) as errorf:
					errorf.write(str(datetime.datetime.now())+" - Well run send error: "+str(e)+"\n")
					errorf.flush()

		if parsed_json['D7'] != D7:  # if signal changed
			if D7 != None:
				remote_watch[str(parsed_json['Time'])] = parsed_json['D7']
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
					#print ('A0 -> HT:'+str(high_temp['A0']), high_temp, file=outf)
					#print ('A0 -> LT:'+str(low_temp['A0']), low_temp, file=outf)
					#print ('A1 -> HB:'+str(high_batt['A1']), high_batt, file=outf)
					#print ('A1 -> LB:'+str(low_batt['A1']), low_batt, file=outf)
					for key, high_value in high_values.items():
						print (str(key)+' high: '+str(high_value[key]), ' low: '+str(low_values[key][key]), file=outf)
					cmd_out = {"DiskSpace":{"Time":str(datetime.datetime.now()),"df":str(output.strip().decode('ascii'))}}
					print (json.dumps(cmd_out)+"\n", file=outf)
					outf.flush()
					sys.stdout.flush()

				with open(floc+check_date+'-serial-summary.log', 'rb') as datafile: # recommended that you open files in binary mode
					# http://stackoverflow.com/questions/16145116/python-requests-post-data-from-a-file
					payload = {'data': datafile.read(), 'type': 'SR', 'upkey': upkey, 'senderid': senderid}
					# headers = {'content-type': 'application/x-www-form-urlencoded'} , headers=headers
					try:
						r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
						print ('Summary upload: '+r.text)
					except requests.exceptions.RequestException as e:
						print ("Summary upload error: "+str(e)+"\n")
						with open(floc+'error.log',fmode) as errorf:
							errorf.write(str(datetime.datetime.now())+" - Summary upload error: "+str(e)+"\n")
							errorf.flush()

				
				#low_temp['A0'] = 1111
				#high_temp['A0'] = 0.0
				#low_batt['A1'] = 1112
				#high_batt['A1'] = 0.0
				# reset trackers
				for i in high_low_tracking:
					high_values[i] = {}
					high_values[i][i] = 0
					low_values[i] = {}
					low_values[i][i] = 100000  # higher then 16 bit a/d

				remote_watch.clear()
			check_date = curr_date
      
		# send heartbeat message
		# or (parsed_json['D6'] == 0): add to trigger when testing
		if ((heartbeat_interval == 'H' and curr_hour != heartbeat_time)
			or (heartbeat_interval == '10M' and curr_minute % 9 != heartbeat_time)
			or (heartbeat_interval == 'M' and curr_minute != heartbeat_time)):
			if (heartbeat_time != None):
				payload = {'data': x, 'type': 'HB', 'upkey': upkey, 'senderid': senderid}
				try:
					r = requests.post(url, data=payload) # auth=('userid', 'password'), if you need it
					print ('Heartbeat message: '+r.text)
				except requests.exceptions.RequestException as e:
					print ("Heartbeat message send error: "+str(e)+"\n")
					with open(floc+'error.log',fmode) as errorf:
						errorf.write(str(datetime.datetime.now())+" - Heartbeat message send error: "+str(e)+"\n")
						errorf.flush()
			if (heartbeat_interval == 'H'):
				heartbeat_time = curr_hour
			if (heartbeat_interval == '10M'):
				heartbeat_time = curr_minute % 9
			if (heartbeat_interval == 'M'):
				heartbeat_time = curr_minute
