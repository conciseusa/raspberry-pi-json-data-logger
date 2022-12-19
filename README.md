# raspberry-pi-json-data-logger
Reads a JSON bit stream made by [Arduino RTC Data Logger and Controller](https://github.com/conciseusa/arduino-rtc-json-data-logger) and process the data and uploads to a remote server. 
Developed for monitoring an off-grid, solar powered well system used at a ranch over a cellular router.
It is now being expanded to other uses such as temperature monitoring, etc.

On a Raspberry Pi, git should already be installed, so the command below should clone the script to your device.
Install git if that is needed on your distro.

`git clone https://github.com/conciseusa/raspberry-pi-json-data-logger.git`

serial_log.ini is used to configure settings such as what remote server to push data to. It is recommended to move up to the parent directory of the checkout and create a directory `config`, copy in serial_log.ini, and configure your settings there. This way a `git pull` will not interact with the ini changes you have made. First ../config will be searched for the serial_log.ini file, then the current dir will be searched.<br>
From the checkout dir:<br>
`mkdir ../config; cp serial_log.ini ../config/serial_log.ini;`<br>
will create the dir and copy the ini file.

Add auto-restart.sh to crontab so at reboot: wait for network to come up and auto restart serial_log.py on errors. See auto-restart.sh

Before adding the auto start code to crontab, it can be useful to run `python3 serial_log.py` in the terminal where you can see error messages. Once everything is working end-to-end, then add the auto start code to crontab.

Add remote-cmd.sh to crontab so diffcult to reach units can be reboot using a file on a web server. See remote-cmd.sh

To show current crontab: `crontab -l`  to edit crontab: `crontab -e`

In theory, all you need is Python, a serial port to receive the data, and a network port to push the data to the target server. Often the biggest challenge is getting connected to the serial port.

**Raspberry Pi/Ubuntu expose log files from a web server**<br>
Caution!! This method provides no security. It is intended to be used on a local network with data that is not sensitive.<br>
A common use for this setup is a remote computer can easily load Pandas DataFrames. Example:<br>
`import pandas as pd`<br>
`df = pd.read_csv('http://192.168.1.111/log/2022-12-18-data.csv')`<br>
The data can then be used in a [Jupyter Notebook](https://jupyter.org/)

raspberry-pi-json-data-logger will look for a log dir in the home dir to write log files to.
If it does not find a log dir, it will write log files to the home dir.
Make sure a log dir is present so it can be exposed:<br>
`mkdir -p  ~/log`<br>
Install a web server:<br>
`sudo apt install apache2 -y`<br>
There should now be a dir that the web server serves files from:<br>
`ls /var/www/html/`<br>
Add a symbolic link from web server to log files:<br>
`sudo ln -s /home/username/log /var/www/html/log` # slashes at the end may not work as expected<br>
Reboot to make sure everything sticks and logs are written to the log dir.
Find the IP address of your device and you should be able to see the logs from another computer.<br>
Example link to enter into a browser: http://192.168.1.111/log/

Bonus: Enable ll command on a Raspberry Pi:
cd ~  
nano .bashrc  
Scroll half way down, where you'll see:  
alias ll='ls -l'  # uncomment to enable, ctrl-o, ctrl-x to save, need to reopen terminal  

[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/conciseusa/raspberry-pi-json-data-logger)
