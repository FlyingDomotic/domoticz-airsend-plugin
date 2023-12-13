#!/bin/bash
NOW=$(date +"%Y%m%d-%H%M%S")
echo "Working in /home/pi/airsend/$NOW/"
mkdir /home/pi/airsend/$NOW
mkdir /home/pi/airsend/$NOW/previous/
curl http://devmel.com/dl/AirSendWebService.tgz --output /home/pi/airsend/$NOW/AirSendWebService.tgz
cd /home/pi/airsend/$NOW/
tar -zxf AirSendWebService.tgz
cd /home/pi/airsend/
/home/pi/airsend/AirSendWebServiceStop.py
sleep 2
cp /home/pi/airsend/AirSendWebService /home/pi/airsend/$NOW/previous/
cp /home/pi/airsend/AirSendWebService.sig /home/pi/airsend/$NOW/previous/
cp /home/pi/airsend/$NOW/bin/unix/arm/AirSendWebService /home/pi/airsend/
cp /home/pi/airsend/$NOW/bin/unix/arm/AirSendWebService.sig /home/pi/airsend/
/home/pi/airsend/AirSendWebServiceStart.py
