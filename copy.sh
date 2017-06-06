#!/bin/bash
#
# This script is initiated by a udev rule in /etc/udev/rules.d/10-local.rules
# which looks for the cruzer usb being plugged in:
#
#   ACTION=="add", ATTRS{product}=="Cruzer Blade", RUN+="/home/pi/pem-pi/copy.sh"
#
# To change to your own device(s) characteristics, use the following command to 
# detail its characteristics and modify the above rule as desired:
#
#  sudo udevadm info -a -p `udevadm info -q path -n /dev/sda1` 
#

# mount drive
sudo mount -o uid=pi,gid=pi /dev/sda1 /mnt/usbstorage

# copy log file and network info to drive
NOW=$(date +"%F")
cp /home/pi/pem-pi/data/temperature_humidity.txt /mnt/usbstorage/temperature_humidity_$NOW.txt
/sbin/ifconfig > /mnt/usbstorage/network.txt

# unmount drive
sudo umount /mnt/usbstorage
