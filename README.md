# pi-env-monitor
Raspberry Pi monitor for environmental conditions in archival storage, using the DHT22 sensor for temperature and humidity data collection.

<img src="https://github.com/prattpi/pi-env-monitor/blob/master/images/monitor.jpg?raw=true" alt="Pi monitor"> 

## Supplies
You will need the following materials:
* Raspberry Pi (tested on Pi 3 B and older B models)
* Mini SD card (16GB minimum) with adapter, and a computer to use to image the initial SD card
* Ethernet cable and wireless network credentials
* Power supply (for the most flexibility in adding future peripherals, an official 5V 2.5A power supply is recommended)
* 16x2 I2C LCD Display and jumper wires (female-to-female) 
* DHT22 temperature-humidity sensor (preferably one already soldered to a PCB board) and jumper wires (female-to-female) 

*Optional Supported Add-ons*

* LED to flash when reading is taken (with 1kΩ resistor), either with breadboard or directly soldered-on wires
* USB drive to copy log files to automatically when inserted 
 
## Getting Started
[Download](https://www.raspberrypi.org/downloads/raspbian/) and [install]( https://www.raspberrypi.org/documentation/installation/installing-images/README.md) the latest *Raspbian Jessie Lite* to your Pi's SD card.

Place a file named *ssh*, without any extension, within the /boot/ partition of the SD card to enable SSH on first boot so the Pi may be run [headless](https://www.raspberrypi.org/documentation/remote-access/ssh/). 

Put in the new SD card, connect the Pi to ethernet and power up. On first boot, change the default password and run a ``sudo apt-get update && sudo apt-get upgrade``. Edit the hostname in /etc/hostname if desired and configure the [wireless settings](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md) for your network. You may also want to run ``sudo raspi-config`` and change the time zone so that dates/times will be appropriate for your location. 

## Sensor & Display Hookups

### LCD Screen
1. Connect power (VCC) to one of the Pi's 5V pins
1. Connect (G)round to one of the Pi's ground pins
1. Connect SDA to the Pi's GPIO2 pin
1. Connect SCL to the Pi's GPIO3 pin

### DHT22 Temperature-humidity Sensor
The DHT22 already soldered to the PCB board will have three pins. They are typically labeled G (GND), V (VCC), and D (Data).
1. Connect power (VCC) to one of the Pi's 3.3V pins
1. Connect (D)ata to one of the Pi's GPIO pins and note the pin number for your particular Pi model
1. Connect (G)round to one of the Pi's ground pins

### [Optional] LED Light
1. The short leg of the LED (-) should be wired to one of the Pi's ground pins
1. The long leg of the LED (+) should be connected to one end of a 1kΩ resistor and then the other end of the resistor connected to a GPIO pin 


## Pi Setup
The completed Pi will perform the following functions: 1) collect temperature and humidity, show the values on the LCD screen, and write the values to a log file every 5 minutes; 2) email an alert if temperature or humidity thresholds are exceeded; and 3) automatically copy the log file to a USB drive, when inserted. 

### 1) Set up data collection and logging

First, we will set up the Adafruit library to read data from the DHT (from https://github.com/adafruit/Adafruit_Python_DHT) by doing the following:
```
cd /home/pi
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python setup.py install
``` 

Next, from the pi user's home directory, clone the pem-pi repository into ``/home/pi/pem-pi``.

To enable the LCD screen, you must first enable the i2c interface by following [these instructions](http://www.raspberrypi-spy.co.uk/2014/11/enabling-the-i2c-interface-on-the-raspberry-pi/). Make sure to run the ``sudo i2cdetect -y 1`` command at the end to determine the device's address. For example, the output below indicates that the lcd is at the (default) *0x3F* address.
```
pi@raspberrypi_pratt:~ $ sudo i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 3f
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

The monitor_dht22.py takes the following arguments, many of which are optional:
```
pi@raspberrypi_pratt2:~/pem-pi $ python monitor_dht22.py -h
usage: monitor_dht22.py [-h] [--led LED] [--max_temp MAX_TEMP]
                        [--min_temp MIN_TEMP] [--max_rh MAX_RH]
                        [--min_rh MIN_RH] [--email EMAIL] [--gsheets]
                        gpio

positional arguments:
  gpio                 Pin num of DHT22 sensor

optional arguments:
  -h, --help           show this help message and exit
  --led LED            Pin num of LED
  --max_temp MAX_TEMP  Maximum acceptable temp, default 70F
  --min_temp MIN_TEMP  Minimum acceptable temp, default 32F
  --max_rh MAX_RH      Maximum acceptable humidity, default 50
  --min_rh MIN_RH      Minimum acceptable humidity, default 30
  --email EMAIL        Email destination for warnings
  --gsheets            Turn on Google Sheets logging, must configure
```

Lastly, edit the crontab via ``crontab -e`` to run the monitor_dht22.py script at the desired interval.  The example given below will run every 5 minutes. Make sure to replace the pin number(s) and destination email with the appropriate ones for your setup. In the crontab example below, the temp sensor is at GPIO 25, the LED is at GPIO 4, emailing is enabled via the address given, and Google Sheets data copying is enabled (more information on this in the notes section at the bottom of README.md). 

```
*/5 * * * * python /home/pi/pem-pi/monitor_dht22.py 25 --led 4 --email youremail@yourdomain.com --gsheets > /home/pi/pem-pi/monitor.err 2>&1
```

### 2) Set up email alerts

The Pi will use ssmtp and a gmail account (you can create a new one for this purpose) to send mail.  To setup, first run:
```
sudo apt-get install ssmtp mailutils
```
Then, as root, edit the config file at ``/etc/ssmtp/ssmtp.conf`` to include your gmail credentials. At a minimum, you'll need to edit or add the following lines:
```
mailhub=smtp.gmail.com:587
hostname=YOUR PI'S HOSTNAME
AuthUser=YOUR EMAIL@gmail.com
AuthPass=YOUR PASSWORD
useSTARTTLS=YES
```
This will be the account used to send email, i.e. the "from" header. To configure the destination email, modify the command-line email argument used in the cron job started at boot (as detailed above).

The Pi will send a maximum of one warning email per day if the conditions exceed the temperature or humidity parameters. The default warning values may be overridden using the optional flags listed above. 

### 3) Set up automatic copying to USB drive on insertion 

Set up a mount point (as detailed [here](https://www.htpcguides.com/properly-mount-usb-storage-raspberry-pi/)):
```
sudo mkdir /mnt/usbstorage
sudo chown -R pi:pi /mnt/usbstorage
sudo chmod -R 775 /mnt/usbstorage
sudo setfacl -Rdm g:pi:rwx /mnt/usbstorage
sudo setfacl -Rm g:pi:rwx /mnt/usbstorage
```
Then create and add the following line to a new ``sudo nano /etc/udev/rules.d/10-local.rules`` file:

```
ACTION=="add", ATTRS{product}=="Cruzer Blade", RUN+="/home/pi/pem-pi/copy.sh"
```
And reload the udev rules:
```
sudo udevadm control --reload-rules
```
This will run the ``/home/pi/pem-pi/copy.sh`` shell script when the *Cruzer Blade* usb drive is plugged in, which will mount the drive, copy the log file and network information to it, then unmount the drive for removal. 

To customize for your own drive(s) the following commands will tell you the attributes for your plugged-in drive, which you can use to modify the above udev rule as desired. 
```
sudo udevadm info -a -p `udevadm info -q path -n /dev/sda1` 
```
## General Notes

You can cram everything into a plastic enclosure, but make sure to use electrical tape or screw in the various components so they don't cause interference or come unplugged. The Pi 3 has a tendency to run warm; depending on the enclosure you are using you can check temp with ``/opt/vc/bin/vcgencmd measure_temp`` and may add a heatsink and/or fan as necessary.

Log file size for temperature, humidity, ratio and concentration is about 15K for 45 hours, so around 8K written per day. So it would take about 125 days to write 1MB of data. 

For easy visualization of the data, Google Sheets with a chart can be configured. Instructions such as the [Adafruit ones here](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/connecting-to-googles-docs-updated) can be followed to set up the Pi to write directly to a Google Sheet which has a live-updated interactive chart that is  publicly accessible. An example of a [Google line chart](https://docs.google.com/spreadsheets/d/16_la0nWrAp0jDzci9beiVVRqLKAv15FRbYsVDINavaM/pubchart?oid=469596806&format=interactive) created with the output data file. If the Pi does not have network access, you can simply copy the data via USB and open the tab-delimited file into a Google Sheet as needed. 

As the Pi gives off heat, the temp sensor seems to be most accurate when placed a few inches from the enclosure, as shown in the picture above. 
