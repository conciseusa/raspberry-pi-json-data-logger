# raspberry-pi-json-data-logger
Reads a JSON bit stream made by conciseusa/arduino-rtc-json-data-logger and process the data and uploads to a remote server. 
Developed for monitoring an off-grid, solar powered well system used at a ranch over a cellular router.
It is now being expanded to other uses such as temperature monitoring, etc.

On a Raspberry Pi, git should already be installed, so the command below should clone the script to your device.
Install git if that is needed on your distro.

`git clone https://github.com/conciseusa/raspberry-pi-json-data-logger.git`

In theory, all you need is Python, a serial port to receive the data, and a network port to push the data to the target server.
