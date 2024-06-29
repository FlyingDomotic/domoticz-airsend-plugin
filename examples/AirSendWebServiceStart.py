#!/usr/bin/python3
import psutil
import time
import os

prcName = 'AirSendWebService'
prcFound = False
os.system('/home/pi/airsend/AirSendWebService')
time.sleep(2)
for pid in psutil.pids():
    try:
        proc = psutil.Process(pid)
        for cmd in proc.cmdline():
            if cmd[-len(prcName):] == prcName:
                print("Started pid "+str(pid)+" "+ cmd) 
                prcFound = True
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        print(e)
if not prcFound:
    print('No '+prcName+' process found...')
