#           AirSend plugin
"""
<plugin key="AirSend" name="AirSend plugin" author="Flying Domotic" version="0.0.1">
    <description>
      AirSend plug-in from Flying Domotic<br/><br/>
      Integrates AirSend devices into Domoticz<br/>
    </description>
    <params>
        <param field="Mode1" label="JSON configuration file to use" width="400px" required="true" default="AirSend.json"/>
        <param field="Mode6" label="Debug" width="400px">
            <options>
                <option label="Extra verbose (Framework logs 2+4+8+16+64 + device dump)" value="Verbose+"/>
                <option label="Verbose (Framework logs 2+4+8+16+64)" value="Verbose"/>
                <option label="Normal (Framework logs 2+4+8)" value="Debug"/>
                <option label="None" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import os
import json
import yaml
import requests
import urllib.parse

# Implements plug-in as class
class BasePlugin:
    debugging = 'Normal'
    yamlDevices = None
    configOk = False
    eventDataName = 'AirSend event data'
    eventDataKey = "0"
    eventDataIdx = 0
    airSendButtonType = 4096
    airSendCoverType = 4097
    airSendCoverPositionType = 4098
    airSendSwitchType = 4099
    airSendCallbackName = 'airsend.php'
    domoticzRootUrl = None
    yamlConfigurationFile = None
    webServerFolder = None
    webServerUrl = None
    webServiceUrl = None
    protocolToListen = None
    authorization = None
    mapping = []
    
    # Returns a dictionary value giving a key or default value if not existing
    def getValue(self, dict, key, default=''):
        if dict == None:
            return default
        else:
            if key in dict:
                if dict[key] == None:
                    return default #or None
                else:
                    return dict[key]
            else:
                return default #or None

    # Return a path in a dictionary or default value if not existing
    def getPathValue (self, dict, path, separator = '/', default=''):
        pathElements = path.split(separator)
        element = dict
        for pathElement in pathElements:
            if pathElement not in element:
                return default
            element = element[pathElement]
        return element

    # Load a dictionary from a YAML file
    def loadYamlDictionary(self, file):
        if os.path.exists(file):
            with open(file, encoding = 'UTF-8') as f:
                return yaml.safe_load(f.read())
        else:
            Domoticz.Error("Can't find configuration file " + file)
            return {}

    # Find a device by ID in devices table
    def getDevice(self, deviceId):
        for device in Devices:
            if (Devices[device].DeviceID == deviceId) :
                # Return device
                return Devices[device]
        # Return None if not found
        return None

    # Find a device ID in YAML configuration file
    def getYamlDevice(self, deviceId):
        for airSendDevice in self.yamlDevices:
            # Get device parameters
            deviceParams = self.yamlDevices[airSendDevice]
            # Key is channel ID + channel source
            deviceKey = str(self.getPathValue(deviceParams, 'channel/id'))+"/"+str(self.getPathValue(deviceParams, 'channel/source'))
            if (deviceKey == deviceId) :
                # Return device
                return deviceParams
        # Return None if not found
        return None

    # Get next free device Id
    def getNextDeviceId(self):
        nextDeviceId = 1
        while True:
            exists = False
            for device in Devices:
                if (device == nextDeviceId) :
                    exists = True
                    break
            if (not exists):
                break;
            nextDeviceId = nextDeviceId + 1
        return nextDeviceId

    # Return device unit and name
    def deviceStr(self, unit):
        name = "<UNKNOWN>"
        if unit in Devices:
            name = Devices[unit].Name
        return format(unit, '03d') + "/" + name

    # Return device unit from device name
    def getUnit(self, device):
        unit = -1
        for k, dev in Devices.items():
            if dev == device:
                unit = k
        return unit

    # Called when plug-in starts
    def onStart(self):
        # Parse options
        self.debugging = Parameters["Mode6"]
        if self.debugging == "Verbose+":
            Domoticz.Debugging(1+2+4+8+16+64)
            self.dumpConfigToLog()
        if self.debugging == "Verbose":
            Domoticz.Debugging(2+4+8+16+64)
            self.dumpConfigToLog()
        if self.debugging == "Debug":
            Domoticz.Debugging(2+4+8)
            self.dumpConfigToLog()

        # Load JSON mapping file
        jsonFile = Parameters['HomeFolder'] + Parameters["Mode1"]
        jsonData = None
        with open(jsonFile, encoding = 'UTF-8') as configStream:
            jsonData = json.load(configStream)
        # Read parameters
        self.domoticzRootUrl = self.getPathValue(jsonData, 'parameters/domoticzRootUrl')
        if not self.domoticzRootUrl:
            Domoticz.Error("Can't find 'domoticzRootUrl' in "+jsonFile)
            return
        self.yamlConfigurationFile = self.getPathValue(jsonData, 'parameters/yamlConfigurationFile')
        if not self.yamlConfigurationFile:
            Domoticz.Error("Can't find 'yamlConfigurationFile' in "+jsonFile)
            return
        self.authorization = self.getPathValue(jsonData, 'parameters/authorization')
        if not self.authorization:
            Domoticz.Error("Can't find 'authorization' in "+jsonFile)
            return
        self.webServiceUrl = self.getPathValue(jsonData, 'parameters/webServiceUrl')
        if not self.webServiceUrl:
            Domoticz.Error("Can't find 'webServiceUrl' in "+jsonFile)
            return
        self.protocolToListen = self.getPathValue(jsonData, 'parameters/protocolToListen')
        self.webServerFolder = self.getPathValue(jsonData, 'parameters/webServerFolder')
        if self.protocolToListen and not self.webServerFolder:
            Domoticz.Error("Can't find 'webServerFolder' in "+jsonFile)
            return
        self.webServerUrl = self.getPathValue(jsonData, 'parameters/webServerUrl')
        if self.protocolToListen and not self.webServerUrl:
            Domoticz.Error("Can't find 'webServerUrl' in "+jsonFile)
            return
        # Read mappings
        self.mappings = {}
        mappingsData = self.getPathValue(jsonData, 'mapping', default=[])

        # Create text device to get events from AirSend PHP callback
        if self.getDevice(self.eventDataKey) == None:
            Domoticz.Log("Creating device " + self.eventDataName)
            Domoticz.Device(Name=self.eventDataName, Unit=self.getNextDeviceId(), Type=243, Subtype=19, DeviceID=self.eventDataKey, Used=False).Create()

        # Get callback text device idx
        self.eventDataIdx = self.getDevice(self.eventDataKey).ID
        Domoticz.Debug(self.eventDataName + " idx is "+ str(self.eventDataIdx))

        # Load YAML mapping file
        yamlFile = Parameters['HomeFolder'] + self.yamlConfigurationFile
        yamlConfigData = None
        yamlConfigData = self.loadYamlDictionary(yamlFile)
        # Abort start if configuration file not found
        if yamlConfigData == {}:
            return

        # Go through YAML file to create devices
        self.yamlDevices = self.getPathValue(yamlConfigData, 'airsend/devices', '/', None)
        if self.yamlDevices == None:
            Domoticz.Error("Can't find 'airsend' 'devices' in "+yamlConfigData)
            return

        for airSendDevice in self.yamlDevices:
            # Get device parameters
            deviceParams = self.yamlDevices[airSendDevice]
            # Get channel parameters
            channel = self.getValue(deviceParams, 'channel')
            Domoticz.Debug("Name "+str(airSendDevice)+', type '+str(self.getValue(deviceParams, 'type'))+', channel '+str(self.getValue(channel, 'id'))+'/'+str(self.getValue(channel, 'source')))
            # Key is channel ID + channel source
            deviceKey = str(self.getValue(channel, 'id'))+"/"+str(self.getValue(channel, 'source'))
            # Create device if not already there
            deviceType = self.getValue(deviceParams, 'type')
            if self.getDevice(deviceKey) == None:
                if  deviceType == self.airSendButtonType:   # Button
                    Domoticz.Log("Creating button " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=244, Subtype=73, Switchtype=0, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendCoverType:  # Cover
                    Domoticz.Log("Creating cover " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=244, Subtype=73, Switchtype=3, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendCoverPositionType:  # Cover with position
                    Domoticz.Log("Creating cover with position " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=244, Subtype=73, Switchtype=21, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendSwitchType:  # Switch
                    Domoticz.Log("Creating switch " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=244, Subtype=73, Switchtype=0, DeviceID=deviceKey, Used=True).Create()
                else:
                    Domoticz.Error("Don't know what "+str(deviceType)+" type could be...")

        # Read all mapping lines
        for mapping in mappingsData:
            # Extract mapping name (useless, here to help reading)
            for mappingKey in mapping:
                # Extract mapping parameters
                mappingData = mapping[mappingKey]
                remoteId = self.getValue(mappingData, 'remoteId')
                if not remoteId:
                    Domoticz.Error("Can't find 'remoteId' in mapping "+mappingKey+' '+mappingData)
                    return
                remoteSource = self.getValue(mappingData, 'remoteSource')
                if not remoteSource:
                    Domoticz.Error("Can't find 'remoteSource' in mapping "+mappingKey+' '+mappingData)
                    return
                deviceId = self.getValue(mappingData, 'deviceId')
                if not deviceId:
                    Domoticz.Error("Can't find 'deviceId' in mapping "+mappingKey+' '+mappingData)
                    return
                deviceSource = self.getValue(mappingData, 'deviceSource')
                if not deviceSource:
                    Domoticz.Error("Can't find 'deviceSource' in mapping "+mappingKey+' '+mappingData)
                    return
            # Add mapping to dictionary (remote key = device key)
            remoteKey = str(remoteId)+'/'+str(remoteSource)
            deviceKey = str(deviceId)+'/'+str(deviceSource)
            device = self.getDevice(deviceKey)
            if device:
                mappingName = device.Name
            else:
                mappingName = "** unkwnown device **"
            Domoticz.Debug('Mapping '+mappingKey+' ('+remoteKey+') to '+mappingName+' ('+deviceKey+')')
            self.mappings[remoteKey] = deviceKey

        # Should set a callback to listen a protocol to?
        if self.protocolToListen:
            # Create callback file from template
            templateFile = Parameters['HomeFolder'] + 'template.php'
            if os.path.exists(templateFile):
                with open(templateFile, 'rt') as f:
                    templateData = f.read()
            else:
                Domoticz.Error("Can't find template file "+templateFile)
                return

            # Replace variable tags in file
            templateData = templateData.replace("##URL##", self.domoticzRootUrl)
            templateData = templateData.replace("##IDX##", str(self.eventDataIdx))

            # Write callback file
            phpFile = self.webServerFolder+self.airSendCallbackName
            try:
                with open(phpFile, 'wt') as f:
                    f.write(templateData)
            except:
                Domoticz.Error("Can't write "+phpFile)
                return
            Domoticz.Debug("Wrote "+phpFile)
            # Set callback protection
            try:
                os.chmod(phpFile, 0o644)
            except:
                Domoticz.Error("Can't protect  "+phpFile)
            # Set the callback
            callbackProtocol = str(self.protocolToListen)
            callbackSpecs = self.webServerUrl+self.airSendCallbackName
            Domoticz.Debug('Binding prototol '+callbackProtocol+' to '+callbackSpecs)
            jsonData = '{"duration": 0, "channel": {"id": '+callbackProtocol+'}, "callback": "'+callbackSpecs+'"}'
            response = requests.post(url=self.webServiceUrl+'airsend/bind' \
                ,headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
                ,data=jsonData \
            )
            if response.status_code != 200:
                Domoticz.Error('Error '+str(response.status_code)+' in POST '+response.url+', data '+str(jsonData))
            else:
                Domoticz.Log(jsonData+ ' returned Ok')

        # Enable heartbeat
        Domoticz.Heartbeat(60)
        self.configOk = True

    # Called when plug-in stops
    def onStop(self):
        configOk =  False
        # remove the callback
        Domoticz.Debug('Removing callback')
        response = requests.get(url=self.webServiceUrl+'airsend/close' \
            ,headers={'Accept': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
        )
        if response.status_code != 200:
            Domoticz.Error('Error '+str(response.status_code)+' in GET '+response.url)
        # Delete PHP callback file
        phpFile = self.webServerFolder+self.airSendCallbackName
        Domoticz.Log("Removing "+phpFile)
        try:
            os.remove(phpFile)
        except:
            pass

    # Called when a command is sent to one device linked to this plug-in
    def onCommand(self, Unit, Command, Level, sColor):
        device = Devices[Unit]
        Domoticz.Log(self.deviceStr(Unit) + ", "+device.DeviceID+": Command: '" + str(Command) + "', Level: " + str(Level) + ", Color:" + str(sColor))
        # Exit if config not ok
        if (self.configOk != True):
            Domoticz.Error('Init not ok, onCommand ignored')
            return
        deviceParams = self.getYamlDevice(device.DeviceID)
        if not deviceParams:
            Domoticz.Error("Can't find "+device.DeviceID+' for '+device.Name+' in '+str(self.yamlDevices))
            return
        # Get device current values
        nValue = device.nValue
        sValue = device.sValue
        airSendType = -1
        airSendValue = -1
        airSendDeviceType = self.getValue(deviceParams, 'type')
        # Update device depending on command
        if Command == 'Off':
            nValue = 0
            if airSendDeviceType == self.airSendSwitchType:
                airSendType = 0
                airSendValue = 19   # Off
            elif airSendDeviceType == self.airSendCoverType or airSendDeviceType == self.airSendCoverPositionType:
                airSendType = 0
                airSendValue = 35   # Up
            else:
                Domoticz.Error("Don't know how to execute "+command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'On':
            nValue = 1
            if airSendDeviceType == self.airSendSwitchType:
                airSendType = 0
                airSendValue = 20   # On
            if airSendDeviceType == self.airSendButtonType:
                airSendType = 0
                airSendValue = 18   # Toggle
            elif airSendDeviceType == self.airSendCoverType or airSendDeviceType == self.airSendCoverPositionType:
                airSendType = 0
                airSendValue = 34   # Down
            else:
                Domoticz.Error("Don't know how to execute "+command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Stop':
            nValue = 17
            if airSendDeviceType == self.airSendCoverType or airSendDeviceType == self.airSendCoverPositionType:
                airSendType = 0
                airSendValue = 17   # Stop
            else:
                Domoticz.Error("Don't know how to execute "+command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Set Level':
            if airSendDeviceType == self.airSendCoverType or airSendDeviceType == self.airSendCoverPositionType:
                airSendType = 9
                airSendValue = Level
            else:
                Domoticz.Error("Don't know how to execute "+command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        else:
            Domoticz.Error('Command: "' + str(Command) + '" not supported yet for ' + device.Name+'. Please ask for support.')
        if airSendType != -1:
            elements = device.DeviceID.split('/')
            jsonData = '{"wait": true, "channel": {"id":"'+elements[0]+'","source":"'+elements[1]+'"}, "thingnotes":{"notes":[{"method":1,"type":'+str(airSendType)+',"value":'+str(airSendValue)+'}]}}'
            response = requests.post(url=self.webServiceUrl+'airsend/transfer' \
                ,headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
                ,data=jsonData \
            )
            if response.status_code != 200:
                Domoticz.Error('Error '+str(response.status_code)+' in POST '+response.url+', data '+str(jsonData))

    # Called when a device is added to this plug-in
    def onDeviceAdded(self, Unit):
        Domoticz.Log("onDeviceAdded " + self.deviceStr(Unit))

    # Called when a device managed by this plug-in is (externally) modified
    def onDeviceModified(self, Unit):
        Domoticz.Log("onDeviceModified " + self.deviceStr(Unit))
        # Exit if config not ok
        if (self.configOk != True):
            Domoticz.Error('Init not ok, onDeviceModified ignored')
            return
        device = Devices[Unit]
        if device.DeviceID == self.eventDataKey:
            # This is an update comming from AirSend device through callback
            event = device.sValue
            Domoticz.Log('Received event '+event)
            jsonEvent = json.loads(event)
            eventType = str(self.getValue(jsonEvent, 'type'))
            # As of now, work only for event type 3 (GOT)
            if eventType != '3':
                Domoticz.Error("Can't understand event type "+eventType+" yet...")
                return
            # Get device Key from id & source
            deviceKey = str(self.getPathValue(jsonEvent, 'channel/id'))+"/"+str(self.getPathValue(jsonEvent, 'channel/source'))
            # Try to map device key
            if deviceKey in self.mappings:
                Domoticz.Debug('Mapping '+deviceKey+' to '+self.mappings[deviceKey])
                deviceKey = self.mappings[deviceKey]
            # Get YAML parameters
            deviceParams = self.getYamlDevice(deviceKey)
            if not deviceParams:
                Domoticz.Error("Can't find "+deviceKey+' in YAML configuration file')
                return
            # Get Domoticz device
            device = self.getDevice(deviceKey)
            if not device:
                Domoticz.Error("Can't find "+deviceKey+' in devices for '+event)
                return
            # Extract notes
            notes = self.getPathValue(jsonEvent,'thingnotes/notes')
            # Extract method, type and value
            eventMethod = self.getValue(notes[0],'method')
            eventType = self.getPathValue(notes[0],'type')
            eventValue = self.getPathValue(notes[0],'value')
            Domoticz.Debug("Device "+device.Name+', method '+str(eventMethod)+', type '+str(eventType)+', value '+str(eventValue))
            # Change Domoticz device depending on AirSend device type
            airSendDeviceType = self.getValue(deviceParams, 'type')
            nValue = None
            sValue = None
            if airSendDeviceType == self.airSendCoverType or airSendDeviceType == self.airSendCoverPositionType:
                if   eventType == 0 and eventValue == 35:   # Up
                    device.Update(nValue=0, sValue = '100')
                elif eventType == 0 and eventValue == 34:   # Down
                    device.Update(nValue=1, sValue = '0')
                elif eventType == 0 and eventValue == 17:   # Stop
                    device.Update(nValue=17, sValue = device.sValue)
                #elif eventType == 0 and eventValue == 22:  # User position (not yet implemented)
                elif eventType == 9:                        # Level in event value
                    if int(eventValue) == 0:
                        device.Update(nValue=1, sValue = '0')
                    elif int(eventValue) == 100:
                        device.Update(nValue=0, sValue = '100')
                    else:
                        device.Update(nValue=2, sValue = str(eventValue))
                else:
                    Domoticz.Error("Can't change AirSend cover type "+str(airSendDeviceType)+' with event type '+str(eventType)+' and event value '+str(eventValue))
                    return
            elif airSendDeviceType == self.airSendSwitchType:
                if   eventType == 0 and eventValue == 19:   # Off
                    device.Update(nValue=0, sValue = device.sValue)
                elif eventType == 0 and eventValue == 20:   # On
                    device.Update(nValue=1, sValue = device.sValue)
                else:
                    Domoticz.Error("Can't change AirSend switch type "+str(airSendDeviceType)+' with event type '+str(eventType)+' and event value '+str(eventValue))
                    return
            elif airSendDeviceType == self.airSendButtonType:
                if   eventType == 0 and eventValue == 18:   # Toggle
                    device.Update(nValue=0 if device.nValue else 1, sValue = device.sValue)
                else:
                    Domoticz.Error("Can't change AirSend button type "+str(airSendDeviceType)+' with event type '+str(eventType)+' and event value '+str(eventValue))
                    return
            else:
                Domoticz.Error("Can't change AirSend device type "+str(airSendDeviceType))
                return

    # Called when a device is removed from this plug-in
    def onDeviceRemoved(self, Unit):
        Domoticz.Log("onDeviceRemoved " + self.deviceStr(Unit))

    # Called when a heartbeat is sent
    def onHeartbeat(self):
        pass

    # Dumps configuration to log
    def dumpConfigToLog(self):
        for x in Parameters:
            if Parameters[x] != "":
                Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
        Domoticz.Log("Device count: " + str(len(Devices)))
        for x in Devices:
            Domoticz.Log("Device: Unit " + str(x) + ", DeviceID " + str(Devices[x].DeviceID) + " - " + str(Devices[x]))

# Forwards all commands/event to BasePlugin
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)

def onDeviceAdded(Unit):
    global _plugin
    _plugin.onDeviceAdded(Unit)

def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)

def onDeviceRemoved(Unit):
    global _plugin
    _plugin.onDeviceRemoved(Unit)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
