# raspberry-pi-json-data-logger
Reads a JSON bit stream made by conciseusa/arduino-rtc-json-data-logger and process the data and uploads to a remote server. 
Developed for monitoring an off-grid, solar powered well system used at a ranch over a cellular router.
It is now being expanded to other uses such as temperature monitoring, etc.

On a Raspberry Pi, git should already be installed, so the command below should clone the script to your device.
Install git if that is needed on your distro.

`git clone https://github.com/conciseusa/raspberry-pi-json-data-logger.git`

serial_log.ini is used to configure settings such as what remote server to push data to. It is recommended to move up to the parent directory of the checkout and create a directory `config`, copy in serial_log.ini, and configure your settings there. This way a `git pull` will not interact with the ini changes you have made. First ../config will be searched for the serial_log.ini file, then the current dir will be searched. From the checkout dir, `mkdir ../config; cp serial_log.ini ../config/serial_log.ini;` will create the dir and copy the ini file.

Add to crontab so at restart: wait for network to come up and auto restart serial_log.py (checkout in /home/pi/git/):

@reboot until ping -c 1 -W 1 8.8.8.8; do sleep 1; done; cd /home/pi/git/raspberry-pi-json-data-logger; while true; do python3 serial_log.py; echo "restarting serial_log"; test $? -gt 128 && break; done;

Before adding the auto start code to crontab, it can be useful to run `python3 serial_log.py` in the terminal where you can see error messages. Once everything is working end-to-end, then add the auto start code to crontab.

To show current crontab: `crontab -l`  to edit crontab: `crontab -e`

In theory, all you need is Python, a serial port to receive the data, and a network port to push the data to the target server. Often the biggest challenge is getting connected to the serial port.

[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/conciseusa/raspberry-pi-json-data-logger)
