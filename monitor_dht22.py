#!/usr/bin/env python
################################
#                              #    
#       monitor_dht22.py       #
#                              #
################################

import lcd_i2c as lcd
import Adafruit_DHT as dht
import RPi.GPIO as GPIO
import subprocess
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import argparse
from datetime import datetime as dt
import socket
import os
import subprocess
import cPickle as pickle

def write_spreadsheet(row):
   try:
      # configure with appropriate google account credentials, e.g. 
      # per https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/connecting-to-googles-docs-updated
      scope = ['https://spreadsheets.google.com/feeds']
      credentials = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/pem-pi/pi-env-monitor-5c9b8e4fc16c.json', scope)
      gc = gspread.authorize(credentials)
      wks = gc.open("pi-env-monitor").sheet1
      wks.append_row(row)
   except:
      print "Spreadsheet connection failed, skipping until next read..."

def send_mail(mailto, temp, humidity):
   try:
      mail_command = 'echo "Environment exceeded temp/humidity thresholds with temperature of '+"{0:.2f}".format(temp)+'F and humidity of '+"{0:.2f}".format(humidity)+'%." | mail -s "Warning - $(date)" '+mailto
      sp = subprocess.Popen(mail_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = sp.communicate()
   except:
      if err:
         return err

def warning_condition(temp,humidity,email=None,max_temp=70.00,min_temp=32.00,max_rh=50.00,min_rh=30.00):
   if not email:
      return False
   if ((temp > max_temp) or (temp < min_temp) or (humidity > max_rh) or (humidity < min_rh)):
      # check if we sent an email today, data in pickle
      file = "/home/pi/pem-pi/sendhist.pickle"
      send_date = {}
      if os.path.isfile(file):
         with open(file, 'rb') as handle:
            send_date = pickle.load(handle)
      d = send_date.get("last_send",None)
      if d != dt.now().strftime('%Y-%m-%d'):
         result = send_mail(email, temp, humidity)
         if not result:
            send_date = { "last_send" : dt.now().strftime('%Y-%m-%d') }
            with open(file, 'wb') as handle:
               pickle.dump(send_date, handle, protocol=pickle.HIGHEST_PROTOCOL)
      return True
   else:
      return False

def main():
   # Accepted arguments
   parser = argparse.ArgumentParser()
   parser.add_argument("gpio", help="Pin num of DHT22 sensor", type=int)
   parser.add_argument("--led", help="Pin num of LED", type=int)
   parser.add_argument("--max_temp", help="Maximum acceptable temp, default 70F", type=float)
   parser.add_argument("--min_temp", help="Minimum acceptable temp, default 32F", type=float)
   parser.add_argument("--max_rh", help="Maximum acceptable humidity, default 50", type=float)
   parser.add_argument("--min_rh", help="Minimum acceptable humidity, default 30", type=float)
   parser.add_argument("--email", help="Email destination for warnings")
   parser.add_argument("--gsheets", help="Turn on Google Sheets logging, must configure",  action='store_true')
   args = parser.parse_args()

   try:
      # get lcd ready
      lcd.lcd_init()
      lcd.lcd_string("Starting monitor",lcd.LCD_LINE_1)
      lcd.lcd_string("script...",lcd.LCD_LINE_2)
      time.sleep(2)
      lcd.lcd_string(time.strftime("%x"),lcd.LCD_LINE_1)
      lcd.lcd_string(time.strftime("%I:%M:%S %p"),lcd.LCD_LINE_2)
      time.sleep(2)
      
      # get led gpio pin ready and flash it
      if args.led:
         GPIO.setmode(GPIO.BCM)
         GPIO.setup(args.led, GPIO.OUT)
         GPIO.output(args.led, True)
         time.sleep(.4)
         GPIO.output(args.led, False)
   
      # Get temp/humidity reading 
      humidity,temp_c = dht.read_retry(dht.DHT22, args.gpio)
      fahr = 9.0/5.0 * temp_c + 32  
   
      # Send reading to LCD
      lcd.lcd_string("Temp={0:0.2f}'F".format(fahr),lcd.LCD_LINE_1)
      lcd.lcd_string("Humidity={0:0.2f}%".format(humidity),lcd.LCD_LINE_2)

      # Check reading for alarm conditions if email is on:
      warned = warning_condition(fahr,humidity,email=args.email,max_temp=args.max_temp or 70.00,
                              min_temp=args.min_temp or 32.00,max_rh=args.max_rh or 50.00,
                              min_rh=args.min_rh or 30.00)

      # Write data to file
      with open("/home/pi/pem-pi/data/temperature_humidity.txt", "a") as myfile:
         myfile.write(dt.now().strftime('%Y-%m-%d %H:%M')+"\t"+"{0:.2f}".format(fahr)+"\t"+"{0:.2f}".format(humidity))
         myfile.write("\n")
         # optionally, send data to google sheets
         if args.gsheets:
            write_spreadsheet([dt.now().strftime('%Y-%m-%d %H:%M'),"{0:.2f}".format(fahr),"{0:.2f}".format(humidity)])

   except KeyboardInterrupt:
      pass
   finally:
      # clean up
      lcd.lcd_byte(0x01, lcd.LCD_CMD)
      GPIO.cleanup()

if __name__ == "__main__":
    main()
