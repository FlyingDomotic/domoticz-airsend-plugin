#!/usr/bin/python3
import psutil
prcName = 'AirSendWebService'
for pid in psutil.pids():
    try:
        proc = psutil.Process(pid)
        for cmd in proc.cmdline():
            if cmd[-len(prcName):] == prcName:
                print("Killing pid "+str(pid)+" "+ cmd) 
                proc.kill()
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        print(e)