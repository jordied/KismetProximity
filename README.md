# WiFi Proximity Scanner
These are a few python files which allow a [Raspberry Pi](https://www.raspberrypi.org) to scan it's surroundings for active Wi-Fi Devices. It shoudl work fine on any Linux device however (untested). Kismet does not work on Macs running *Mavericks or newer*

## Requirements
#### 1. [Kismet](http://kismetwireless.net) 

This must be installed on your Raspberry Pi  or linux device for it to run. **I recomend downloading, compiling and installing yourself from source.** I noticed 
`sudo apt-get kismet` would sometimes install the 2008 version which may not work.

#### 2. [Paho MQTT](https://pypi.python.org/pypi/paho-mqtt)

This can be installed using `sudo pip install paho-mqtt`

## Usage
`sudo python thesis.py`

*Optional Arguements*

`-s %d` sets the scan duration in seconds. where `%d` is the number of seconds.

`-w %d` sets the wait duration in seconds. where `%d` is the number of seconds. This is the wait in between each scan.




