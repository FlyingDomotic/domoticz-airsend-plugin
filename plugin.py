#           AirSend plugin
"""
<plugin key="AirSend" name="AirSend plugin" author="Flying Domotic" version="0.0.12">
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

# Implements plug-in as class
class BasePlugin:
    # Global variables
    debugging = 'Normal'
    airSendCallbackName = 'airsend.php'
    eventDataName = 'AirSend event data'
    eventDataKey = "0"
    eventDataIdx = 0
    authorization = None
    configOk = False
    domoticzRootUrl = None
    protocolToListen = None
    yamlConfigurationFile = None
    yamlDevices = None
    webServerFolder = None
    webServerUrl = None
    webServiceUrl = None
    mapping = []

    # AirSend remote types
    airSendRemoteTypeButton = 4096
    airSendRemoteTypeSwitch = 4097
    airSendRemoteTypeCover = 4098
    airSendRemoteTypeCoverPosition = 4099
    # AirSend event types
    airSendEventTypePending = 0
    airSendEventTypeSent = 1
    airSendEventTypeAck = 2
    airSendEventTypeGot = 3
    airSendEventTypeUnknown = 256
    airSendEventTypeNetwork = 257
    airSendEventTypeSynchronization = 258
    airSendEventTypeSecurity = 259
    airSendEventTypeBusy = 260
    airSendEventTypeTimeout = 261
    airSendEventTypeUnsupported = 262
    airSendEventTypeIncomplete = 263
    airSendEventTypeFull = 264
    # AirSend note type
    airSendNoteTypeState = 0
    airSendNoteTypeData = 1
    airSendNoteTypeTemperature = 2
    airSendNoteTypeIlluminance = 3
    airSendNoteTypeR_humidity = 4
    airSendNoteTypeLevel = 9
    # AirSend note values (commands)
    airSendNoteValuePing = 1
    airSendNoteValueProg = 2
    airSendNoteValueUnprog = 3
    airSendNoteValueReset = 4
    airSendNoteValueStop = 17
    airSendNoteValueToggle = 18
    airSendNoteValueOff = 19
    airSendNoteValueOn = 20
    airSendNoteValueClose = 21
    airSendNoteValueOpen = 22
    airSendNoteValueMiddle = 33
    airSendNoteValueDown = 34
    airSendNoteValueUp = 35
    airSendNoteValueLeft = 36
    airSendNoteValueRight = 37
    airSendNoteValueUserposition = 38

    # Domoticz nValues and sValues
    nValueOff = 0
    sValueOff = '0'
    nValueOpen = nValueOff
    sValueOpen = sValueOff
    nValueOn = 1
    sValueOn = '100'
    nValueClose = nValueOn
    sValueClose = sValueOn
    nValueLevel = 2
    nValueUserPosition = nValueLevel
    sValueUserPosition = '50'
    nValueStop = 17

    # Domoticz types, sub types and switch types
    pTypeGeneralSwitch = 0xF4
    sSwitchGeneralSwitch = 0x49
    STYPE_OnOff = 0
    STYPE_Blinds = 3
    STYPE_PushOn = 9
    STYPE_BlindsPosition = 21

    # HTTP status codes
    htppStatusOk = 200
 
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
            if (Devices[device].DeviceID == deviceId):
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
            if (deviceKey == deviceId):
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
                if (device == nextDeviceId):
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
            Domoticz.Error("Can't find 'airsend' 'devices' in "+str(yamlConfigData))
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
                if  deviceType == self.airSendRemoteTypeButton:   # Button
                    Domoticz.Log("Creating button " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=self.pTypeGeneralSwitch, Subtype=self.sSwitchGeneralSwitch, Switchtype=self.STYPE_PushOn, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendRemoteTypeCover:  # Cover
                    Domoticz.Log("Creating cover " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=self.pTypeGeneralSwitch, Subtype=self.sSwitchGeneralSwitch, Switchtype=self.STYPE_Blinds, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendRemoteTypeCoverPosition:  # Cover with position
                    Domoticz.Log("Creating cover with position " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=self.pTypeGeneralSwitch, Subtype=self.sSwitchGeneralSwitch, Switchtype=self.STYPE_BlindsPosition, DeviceID=deviceKey, Used=True).Create()
                elif deviceType == self.airSendRemoteTypeSwitch:  # Switch
                    Domoticz.Log("Creating switch " + airSendDevice)
                    Domoticz.Device(Name=airSendDevice, Unit=self.getNextDeviceId(), Type=self.pTypeGeneralSwitch, Subtype=self.sSwitchGeneralSwitch, Switchtype=self.STYPE_OnOff, DeviceID=deviceKey, Used=True).Create()
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
            if self.protocolToListen:
                callbackProtocol = str(self.protocolToListen)
                callbackSpecs = self.webServerUrl+self.airSendCallbackName
                Domoticz.Debug('Binding prototol '+callbackProtocol+' to '+callbackSpecs)
                jsonData = '{"duration": 0, "channel": {"id": '+callbackProtocol+'}, "callback": "'+callbackSpecs+'"}'
                localUrl = self.webServiceUrl+'airsend/bind'
                try:
                    response = requests.post(url=localUrl \
                        ,headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
                        ,data=jsonData \
                    )
                except requests.exceptions.RequestException as e:
                    Domoticz.Error('Error posting '+str(jsonData)+' to '+localUrl+': '+str(e))
                else:
                    if response.status_code != self.htppStatusOk:
                        Domoticz.Error('Error '+str(response.status_code)+' in POST '+response.url+', data '+str(jsonData))
                    else:
                        Domoticz.Log(jsonData+ ' returned Ok')

        # Enable heartbeat
        Domoticz.Heartbeat(60)
        self.configOk = True

    # Called when plug-in stops
    def onStop(self):
        self.configOk =  False
        # remove the callback
        Domoticz.Debug('Removing callback')
        localUrl = self.webServiceUrl+'airsend/close'
        try:
            response = requests.get(localUrl \
                ,headers={'Accept': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
            )
        except requests.exceptions.RequestException as e:
            Domoticz.Error('Error getting '+localUrl+': '+str(e))
        else:
            if response.status_code != self.htppStatusOk:
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
            nValue = self.nValueOff
            sValue = self.sValueOff
            if airSendDeviceType == self.airSendRemoteTypeSwitch:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueOff   # Off
            elif airSendDeviceType == self.airSendRemoteTypeButton:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueToggle   # Toggle
            elif airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueUp   # Up
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'On':
            nValue = self.nValueOn
            sValue = self.sValueOn
            if airSendDeviceType == self.airSendRemoteTypeSwitch:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueOn   # On
            elif airSendDeviceType == self.airSendRemoteTypeButton:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueToggle   # Toggle
            elif airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueDown   # Down
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Stop':
            nValue = self.nValueStop
            if airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueStop   # Stop
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Open':
            nValue = self.nValueOpen
            sValue = self.sValueOpen
            if airSendDeviceType == self.airSendRemoteTypeSwitch:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueOn   # On
            elif airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueUp   # Up
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Close':
            nValue = self.nValueClose
            sValue = self.sValueClose
            if airSendDeviceType == self.airSendRemoteTypeSwitch:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueOff   # Off
            elif airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeState
                airSendValue = self.airSendNoteValueDown   # Down
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        elif Command == 'Set Level':
            nValue = self.nValueLevel
            sValue = str(Level)
            if airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                airSendType = self.airSendNoteTypeLevel
                airSendValue = Level
            else:
                Domoticz.Error("Don't know how to execute "+Command+" for type " + str(airSendDeviceType)+" on "+device.Name)
        else:
            Domoticz.Error('Command: "' + str(Command) + '" not supported yet for ' + device.Name+'. Please ask for support.')
        if airSendType != -1:
            elements = device.DeviceID.split('/')
            jsonData = '{"wait": true, "channel": {"id":"'+elements[0]+'","source":"'+elements[1]+'"}, "thingnotes":{"notes":[{"method":1,"type":'+str(airSendType)+',"value":'+str(airSendValue)+'}]}}'
            localUrl = self.webServiceUrl+'airsend/transfer'
            try:
                response = requests.post(url=localUrl
                    ,headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
                    ,data=jsonData \
                )
                device.Update(nValue=nValue, sValue = sValue)
            except requests.exceptions.RequestException as e:
                Domoticz.Error('Error posting '+str(jsonData)+' to '+localUrl+':'+str(e))
            else:
                if response.status_code != self.htppStatusOk:
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
            if eventType != str(self.airSendEventTypeGot):
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
            eventNoteMethod = self.getValue(notes[0],'method')
            eventNoteType = self.getPathValue(notes[0],'type')
            eventValue = self.getPathValue(notes[0],'value')
            Domoticz.Debug("Device "+device.Name+', method '+str(eventNoteMethod)+', type '+str(eventNoteType)+', value '+str(eventValue))
            # Change Domoticz device depending on AirSend device type
            airSendDeviceType = self.getValue(deviceParams, 'type')
            if airSendDeviceType == self.airSendRemoteTypeCover or airSendDeviceType == self.airSendRemoteTypeCoverPosition:
                if eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueUp:   # Up
                    device.Update(nValue=self.nValueOpen, sValue = self.sValueOpen)
                elif eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueUserposition:   # User position
                    device.Update(nValue=self.nValueUserPosition, sValue = self.sValueUserPosition)
                elif eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueDown:   # Down
                    device.Update(nValue=self.nValueClose, sValue = self.sValueClose)
                elif eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueStop:   # Stop
                    device.Update(nValue=self.nValueStop, sValue = device.sValue)
                elif eventNoteType == self.airSendNoteTypeLevel:                       # Level in event value
                    if int(eventValue) == 0:
                        device.Update(nValue=self.nValueOff, sValue = self.sValueOff)
                    elif int(eventValue) == 100:
                        device.Update(nValue=self.nValueOn, sValue = self.sValueOn)
                    else:
                        device.Update(nValue=self.nValueLevel, sValue = str(eventValue))
                else:
                    if eventNoteType == self.airSendNoteTypeData:  # Ignore event type 1 (DATA)
                        Domoticz.Debug("Ignoring change airSend cover type "+str(airSendDeviceType)+' with event type '+str(eventNoteType)+' and event value '+str(eventValue)+' for '+device.Name)
                    else:
                        Domoticz.Error("Can't change airSend cover type "+str(airSendDeviceType)+' with event type '+str(eventNoteType)+' and event value '+str(eventValue)+' for '+device.Name)
                    return
            elif airSendDeviceType == self.airSendRemoteTypeSwitch:
                if eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueOff:   # Off
                    device.Update(nValue=self.nValueOff, sValue = self.sValueOff)
                elif eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueOn:   # On
                    device.Update(nValue=self.nValueOn, sValue = self.sValueOn)
                else:
                    Domoticz.Error("Can't change airSend switch type "+str(airSendDeviceType)+' with event type '+str(eventNoteType)+' and event value '+str(eventValue)+' for '+device.Name)
                    return
            elif airSendDeviceType == self.airSendRemoteTypeButton:
                if eventNoteType == self.airSendNoteTypeState and eventValue == self.airSendNoteValueToggle:   # Toggle
                    device.Update(nValue=self.nValueOff if device.nValue else self.nValueOn, sValue = self.sValueOff if device.nValue else self.sValueOn)
                else:
                    Domoticz.Error("Can't change airSend button type "+str(airSendDeviceType)+' with event type '+str(eventNoteType)+' and event value '+str(eventValue)+' for '+device.Name)
                    return
            else:
                Domoticz.Error("Can't change airSend device type "+str(airSendDeviceType)+' for '+device.Name)
                return

    # Called when a device is removed from this plug-in
    def onDeviceRemoved(self, Unit):
        Domoticz.Log("onDeviceRemoved " + self.deviceStr(Unit))

    # Called when a heartbeat is sent
    def onHeartbeat(self):
        # Exit if config not ok
        if (self.configOk != True):
            Domoticz.Error('Init not ok, onHeartbeat ignored')
            return
        # Set the callback
        if self.protocolToListen:
            callbackProtocol = str(self.protocolToListen)
            callbackSpecs = self.webServerUrl+self.airSendCallbackName
            jsonData = '{"duration": 0, "channel": {"id": '+callbackProtocol+'}, "callback": "'+callbackSpecs+'"}'
            localUrl = self.webServiceUrl+'airsend/bind'
            try:
                response = requests.post(localUrl
                    ,headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer '+self.authorization}\
                    ,data=jsonData \
                )
            except requests.exceptions.RequestException as e:
                Domoticz.Error('Error posting '+str(jsonData)+' to '+localUrl+':'+str(e))
            else:
                if response.status_code != self.htppStatusOk:
                    Domoticz.Error('Error '+str(response.status_code)+' in POST '+response.url+', data '+str(jsonData))

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
