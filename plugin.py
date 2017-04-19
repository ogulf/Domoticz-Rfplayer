#		   ZiBlue RfPlayer Plugin
#
#		   Author:	 zaraki673/Drooz, 2017
#
#################################################################################################
#################################################################################################
#
#TODO :
#  - infotype 9 , 10 et 11
#  - gestion des erreurs d absences de tag json
#  - gestion des type DIM pour les suptype 0 et 1
#  - verification des type et subtype des devices utilisés
#  - verification des data inserer
#  - ajout Mode configuration pour le mode transcoder (en attente de pouvoir avoir acces a une page de conf pour les plugins python)
#
#################################################################################################
#################################################################################################
#
"""
<plugin key="RFplayer" name="RFplayer" author="zaraki673 - Drooz" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/Ziblue-RFPlayer.html" externallink="http://rfplayer.com/">
	<params>
		<param field="SerialPort" label="Serial Port" width="150px" required="true" default=""/>
		<param field="mode1" label="Mac Address" width="200px" required="true" default="123456765"/>
		<param field="Mode4" label="Enable Learning Mode" width="75px">
			<options>
				<option label="Enable" value="True"/>
				<option label="Disable" value="False"  default="true" />
			</options>
		</param>
		<param field="Mode5" label="Fake Test" width="75px">
			<options>
				<option label="True" value="True"/>
				<option label="False" value="False"  default="true" />
			</options>
		</param>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal"  default="true" />
			</options>
		</param>
	</params>
</plugin>
"""
import Domoticz
import datetime
import json

global ReqRcv


class BasePlugin:

	
	lastHeartbeat = datetime.datetime.now()
	
	def __init__(self):
		return

	def onStart(self):
		global ReqRcv
		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)
	#	if (len(Devices) == 0):
	#		Options = {"LevelActions": "||||||||||||||",
	#					"LevelNames": "Off|VISIONIC433|VISIONIC866|CHACON|DOMIA|X10|X2DSHUTTER|X2DELELC|X2DGAS|RTS|BLYSS|PARROT|KD101",
	#					"LevelOffHidden": "True",
	#					"SelectorStyle": "1"}
	#		Domoticz.Device(Name="Add Light/Switch A-P 1-16 form",  Unit=1, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
	#		Options = {"LevelActions": "||||||||||||||",
	#					"LevelNames": "Off|VISIONIC433|VISIONIC866|CHACON|DOMIA|X10|X2DSHUTTER|X2DELELC|X2DGAS|RTS|BLYSS|PARROT|KD101",
	#					"LevelOffHidden": "True",
	#					"SelectorStyle": "1"}
	#		Domoticz.Device(Name="Add Light/Switch X10 form",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
	#		Domoticz.Log("Devices created.")
	#	Domoticz.Log("Plugin has " + str(len(Devices)) + " devices associated with it.")
		DumpConfigToLog()
		Domoticz.Transport("Serial", Parameters["SerialPort"], Baud=115200)
		Domoticz.Protocol("None")  # None,XML,JSON,HTTP
		Domoticz.Connect()
		ReqRcv=''    
		with open(Parameters["HomeFolder"]+"Response.txt", "wt") as text_file:
			print("Started recording message for debug.", file=text_file)
		return
	
	# present de base 
	def onStop(self):
		#Domoticz.disconnect()
		Domoticz.Log("Plugin is stopping.")

	# present de base 
	def onConnect(self, Status, Description):
		global isConnected
		if (Status == 0):
			isConnected = True
			Domoticz.Log("Connected successfully to: "+Parameters["SerialPort"])
			# Run RFPlayer configuration
			RFpConf()
		else:
			Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"])
			Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"]+" with error: "+Description)
		return True

	# present de base 
	def onMessage(self, Data, Status, Extra):
		global Tmprcv
		global ReqRcv
		###########################################
		Tmprcv=Data.decode(errors='ignore')
		################## check if more than  sec between two message, if yes clear ReqRcv
		lastHeartbeatDelta = (datetime.datetime.now()-self.lastHeartbeat).total_seconds()
		if (lastHeartbeatDelta > 1):
			ReqRcv=''
			Domoticz.Debug("Last Message was "+str(lastHeartbeatDelta)+" seconds ago, Message clear")
		#Wait not end of data '\r'
		if Tmprcv.endswith('\r',0,len(Tmprcv))==False :
			ReqRcv+=Tmprcv
		else : # while end of data is receive
			ReqRcv+=Tmprcv
			#ReqRcv=ReqRcv.replace(",", "")
			
			if ReqRcv.startswith("ZIA--{"):
				Domoticz.Debug(ReqRcv)
				ReadConf(ReqRcv)
			if ReqRcv.startswith("ZIA33"):
				Domoticz.Debug(ReqRcv)
				ReadData(ReqRcv)
			ReqRcv=''
		self.lastHeartbeat = datetime.datetime.now()
		return

	# present de base action executer qd une commande est passé a Domoticz
	def onCommand(self, Unit, Command, Level, Hue):
		SendtoRfplayer(Unit, Command, Level, Hue)
		return True

	def onDisconnect(self):
		return

	def onHeartbeat(self):
		if Parameters["Mode5"] == "True":
			faketest()
		return True

	def SetSocketSettings(self, power):
		return

	def GetSocketSettings(self):
		return

	def genericPOST(self, commandName):
		return
 

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Status, Description):
	global _plugin
	_plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
	global _plugin
	_plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect():
	global _plugin
	_plugin.onDisconnect()

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()


# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:		   " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:	   '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	" + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return	

def UpdateDevice(Unit, nValue, sValue, Image, SignalLevel, BatteryLevel):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	if (Unit in Devices):
		if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].Image != Image) or (Devices[Unit].SignalLevel != SignalLevel) or (Devices[Unit].BatteryLevel != BatteryLevel) :
			Devices[Unit].Update(nValue, str(sValue),Image, SignalLevel, BatteryLevel)
			Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' SignalLevel:"+str(SignalLevel)+" batteryLevel:'"+str(BatteryLevel)+"%' ("+Devices[Unit].Name+")")
	return

	
	
	
	
	
def RFpConf():
	###################Configure Rfplayer ~##################
	lineinput='ZIA++RECEIVER + *'
	Domoticz.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++FORMAT JSON'
	Domoticz.Send(bytes(lineinput + '\n\r','utf-8'))
	lineinput='ZIA++SETMAC ' + Parameters["Mode1"]
	Domoticz.Send(bytes(lineinput + '\n\r','utf-8'))
	return
	
def ReadConf(ReqRcv):
	global RfPmac
	ReqRcv=ReqRcv.replace("ZIA--", "")
	DecData = json.loads(ReqRcv)
	RfPmac = DecData['systemStatus']['info'][2]['v']
	Domoticz.Log('rfp1000 mac :' + str(RfPmac))
	return RfPmac
	
	
def ReadData(ReqRcv):
	##############################################################################################################
	# decoding data from RfPlayer 
	##############################################################################################################
	ReqRcv=ReqRcv.replace("ZIA33", "")
	try:
		DecData = json.loads(ReqRcv)
	except:
		Domoticz.Log("Error while decoding JSON")
		
	infoType = DecData['frame']['header']['infoType']
	Domoticz.Debug("infoType : " + infoType)
	IsCreated=False
	x=0
	nbrdevices=1
	##############################################################################################################
	#####################################Frame infoType 0					ON/OFF
	##############################################################################################################
	if infoType == "0":
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + id)
		
		Options = {"infoType":infoType, "id": str(id), "protocol": str(protocol)}
		Domoticz.Debug("Options to find or set : " + str(Options))
		#########check if devices exist ####################
		for x in Devices:
			if Devices[x].Options == Options :
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		########### create device if not find ###############
		if IsCreated == False and Parameters["Mode4"] == "True" :
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name=protocol + " - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType),Options = Options)
		elif IsCreated == True :
		############ update device if found###################
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType))
	##############################################################################################################
	#####################################Frame infoType 1					ON/OFF   error in API receive id instead of id_lsb and id_msb
	##############################################################################################################
	if infoType == "1":
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		Domoticz.Debug("id : " + id)
		#########################################################################################
		######################### calcul id_lsb and id_msb from id ##############################
		#########################################################################################
		idb= bin(int(id))[2:]
		Domoticz.Debug("id binary : " + str(idb))
		Unit=idb[-6:]
		idd=idb[:-6]
		Domoticz.Debug("Unit b: " + str(Unit))
		Domoticz.Debug("id decode b: " + str(idd))
		Domoticz.Debug("Unit i: " + str(int(Unit,2)+1))
		Domoticz.Debug("id decode i: " + str(int(idd,2)))
		Domoticz.Debug("id decode h: " + str(hex(int(idd,2)))[2:])
		#########################################################################################
		#########################################################################################
		
		Options = {"infoType":infoType, "id": str(id), "id_lsb": str(hex(int(idd,2)))[2:], "id_msb": str(int(Unit,2)+1), "protocol": str(protocol)}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options :
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name=protocol + " - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue =int(SubType),sValue = str(SubType))
	##############################################################################################################
	#####################################Frame infoType 2					Visonic###############################
	#############http://www.el-sys.com.ua/wp-content/uploads/MCR-300_UART_DE3140U0.pdf ###########################
	###########http://cpansearch.perl.org/src/BEANZ/Device-RFXCOM-1.142010/lib/Device/RFXCOM/Decoder/Visonic.pm ##
	#############https://forum.arduino.cc/index.php?topic=289554.0 ###############################################
	##############################################################################################################
	if infoType == "2":
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id_lsb = DecData['frame']['infos']['id_lsb']
		id_msb = DecData['frame']['infos']['id_msb']
		qualifier = list(bin(DecData['frame']['infos']['qualifier'])[2:])
		Domoticz.Debug("id_lsb : " + id_lsb + " id_msb : " + id_msb + " subType :" + SubType)
		##############################################################################################################
		if SubType == "0" : # Detector/sensor
			Tamper=qualifier[0]
			Alarm=qualifier[1]
			Battery=qualifier[2]
			if Tamper=="0" and Alarm=="0" :
				status=0
			if Tamper=="1" and Alarm=="0" :
				status=10
			if Tamper=="0" and Alarm=="1" :
				status=20
			if Tamper=="1" and Alarm=="1" :
				status=30
			if Battery=="0" :
				Battery=100
			else :
				Battery=5
			Options = {"infoType":infoType, "id_lsb": str(id_lsb), "id_msb": str(id_msb), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "||||", "LevelNames": "Off|Tamper|Alarm|Tamper+Alarm", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				#Options = {"LevelActions": "||||", "LevelNames": "Off|Tamper|Alarm|Tamper+Alarm", "LevelOffHidden": "False", "SelectorStyle": "0"}
				Domoticz.Device(Name=protocol + " - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery, Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery)
		##############################################################################################################
		elif SubType == "1":  # remote
			Battery=qualifier[2]
			Signal=qualifier[0] + qualifier[1]
			button1=qualifier[4]
			button2=qualifier[5]
			button3=qualifier[6]
			button4=qualifier[7]
			Options = {"infoType":infoType, "id_lsb": str(id_lsb), "id_msb": str(id_msb), "protocol": str(protocol), "subType": str(SubType), "button": "1"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				Domoticz.Device(Name="Button 1 - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery, Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery)
			###########################################################################################################################
			IsCreated=False
			Options = {"infoType":infoType, "id_lsb": str(id_lsb), "id_msb": str(id_msb), "protocol": str(protocol), "subType": str(SubType), "button": "2"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				Domoticz.Device(Name="Button 2 - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery, Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery)
			############################################################################################################################
			IsCreated=False
			Options = {"infoType":infoType, "id_lsb": str(id_lsb), "id_msb": str(id_msb), "protocol": str(protocol), "subType": str(SubType), "button": "3"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				Domoticz.Device(Name="Button 3 - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery, Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery)
			###################################################################################################################################
			IsCreated=False
			Options = {"infoType":infoType, "id_lsb": str(id_lsb), "id_msb": str(id_msb), "protocol": str(protocol), "subType": str(SubType), "button": "4"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				Domoticz.Device(Name="Button 4 - " + id, Unit=nbrdevices, Type=16, Switchtype=0).Create()
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery, Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue =1,sValue = str(status), BatteryLevel = Battery)
	##############################################################################################################
	#####################################Frame infoType 3				RTS     ##################################
	##############################################################################################################
	if infoType == "3":
		protocol = DecData['frame']['header']['protocol']
		SubType = DecData['frame']['infos']['subType']
		id = DecData['frame']['infos']['id']
		qualifier = DecData['frame']['infos']['qualifier']
		if SubType == "0" :
			if qualifier == "1" :
				level = 0
			elif qualifier == "4" :
				level = 10
			elif qualifier == "7" :
				level = 20
			elif qualifier == "13" :
				level = 30 
			else :
				Domoticz.Log("Unknow qualifier - please send log to dev team")
			#################################################################################################################
			Domoticz.Debug("id : " + id)		
			Options = {"infoType": infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "|||||", "LevelNames": "Off/Down|My|On/Up|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1
				#Options = {"LevelActions": "|||||", "LevelNames": "Off/Down|My|On/Up|Assoc", "LevelOffHidden": "False", "SelectorStyle": "0"}
				Domoticz.Device(Name=" RTS - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue = 1,sValue = str(level),Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 1,sValue = str(level))
				#Devices[nbrdevices].Update(nValue = 1,sValue = "0")
			###############################################################################################################
		elif SubType == "1" :
			if qualifier == "5" :
				level = 10
			elif qualifier == "6" :
				level = 20
			else :
				Domoticz.Log("Unknow qualifier - please send log to dev team")

			Domoticz.Debug("id : " + id)
			#####################################################################################################################
			Options = {"infoType": infoType, "id": str(id), "protocol": str(protocol), "subType": str(SubType), "LevelActions": "||||", "LevelNames": "Off|Left button|Right button", "LevelOffHidden": "False", "SelectorStyle": "0"}
			Domoticz.Debug("Options to find or set : " + str(Options))
			for x in Devices:
				if Devices[x].Options == Options :
					IsCreated = True
					Domoticz.Log("Devices already exist. Unit=" + str(x))
					Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
					nbrdevices=x
				if IsCreated == False :
					nbrdevices=x
			if IsCreated == False and Parameters["Mode4"] == "True":
				nbrdevices=nbrdevices+1				
				#Options = {"LevelActions": "||||", "LevelNames": "Off|Left button|Right button", "LevelOffHidden": "False", "SelectorStyle": "0"}
				Domoticz.Device(Name=" RTS - " + id,  Unit=nbrdevices, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Devices[nbrdevices].Update(nValue = 1,sValue = "0",Options = Options)
			elif IsCreated == True :
				Devices[nbrdevices].Update(nValue = 1,sValue = str(level))
				#Devices[nbrdevices].Update(nValue = 1,sValue = "0")
		else :
			Domoticz.Log("Unknow SubType - please send log to dev team")

	##############################################################################################################
	#####################################Frame infoType 4		Oregon thermo/hygro sensors  #####################
	#############http://www.connectingstuff.net/blog/encodage-protocoles-oregon-scientific-sur-arduino/###########
	##############################################################################################################
	if infoType == "4":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			temp = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			temp = "0"
		try :
			hygro = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			hygro = "0"
		temphygro = temp + ';' + hygro + ';1'

		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Temp - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temp),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temp))
		#####################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Hygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Hygro - " + adr_channel, Unit=nbrdevices, Type=81, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1",Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1")
		#####################################################################################################################	
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel, Unit=nbrdevices, Type=82, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temphygro),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 1,sValue = str(temphygro))

	##############################################################################################################
	#####################################Frame infoType 5		Oregon thermo/hygro/pressure sensors  ############
	##############################################################################################################
	if infoType == "5":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			temp = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			temp = "0"
		try :
			hygro = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			hygro = "0"
		try :
			pressure = DecData['frame']['infos']['measures'][2]['value']
		except IndexError:
			pressure = "0"
		temphygro = temp + ';' + hygro + ';1'
		temphygropress = temphygro + ';' + pressure + ';1'

		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Temp - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp))
		#####################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Hygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Hygro - " + adr_channel, Unit=nbrdevices, Type=81, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1",Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = int(hygro),sValue = "1")
		#####################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Pressure" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Pressure - " + adr_channel, Unit=nbrdevices, Type=243, Subtype=26, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(pressure),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(pressure)+";0")
		#####################################################################################################################	
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygro" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel, Unit=nbrdevices, Type=82, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygro),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygro))
		#####################################################################################################################	
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "TempHygropressure" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Temp/Hygro - " + adr_channel, Unit=nbrdevices, Type=84, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygropress),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(temphygropress))

	##############################################################################################################
	#####################################Frame infoType 6		Oregon Wind sensors  #############################
	#############http://www.connectingstuff.net/blog/encodage-protocoles-oregon-scientific-sur-arduino/###########
	##############################################################################################################
	if infoType == "6":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			speed = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			speed = "0"
		try:
			direction = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			direction = "0"
		if 22 <= int(direction) << 68 : 
			sens = 'NE'
		if 68 <= int(direction) << 112 : 
			sens = 'E'
		if 112 <= int(direction) << 157 : 
			sens = 'SE'
		if 157 <= int(direction) <= 202 : 
			sens = 'S'
		if 202 <= int(direction) <= 247 : 
			sens = 'SO'
		if 247 <= int(direction) <= 292 : 
			sens = 'O'
		if 292 <= int(direction) <= 337 : 
			sens = 'NO'
		if 337 <= int(direction) or int(direction) <= 22 : 
			sens = 'N'
		
		Wind = direction + ';' + sens + ';' + speed + ';0;0;0' #form need : 0;N;0;0;0;0

		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Wind" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True" :
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Wind - " + adr_channel, Unit=nbrdevices, Type=86, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Wind),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Wind))
	
	##############################################################################################################
	#####################################Frame infoType 7		Oregon UV sensors  ############
	##############################################################################################################
	if infoType == "7":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		UV = DecData['frame']['infos']['measures'][0]['value']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "UV" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="UV - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(int(UV)/10) + ';0',Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(int(UV)/10) + ';0')
	
	##############################################################################################################
	#####################################Frame infoType 8		OWL Energy/power sensors  ############
	##############################################################################################################
	if infoType == "8":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		
		Energy = DecData['frame']['infos']['measures'][0]['value']   #♣ watt/hour
		Power = DecData['frame']['infos']['measures'][1]['value']  #♣ total watt with u=230v
		P1 = DecData['frame']['infos']['measures'][2]['value']   #♣ watt with u=230v
		P2 = DecData['frame']['infos']['measures'][3]['value']   #♣ watt with u=230v
		P3 = DecData['frame']['infos']['measures'][4]['value']   #♣ watt with u=230v

		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		##################################################################################################################################
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Power&Energie" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="Power & Energie - " + adr_channel, Unit=nbrdevices, Type=243, Subtype =29, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Power + ';' + Energy),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(Power + ';' + Energy))		
		##################################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P1" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="P1 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P1),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P1))
		##################################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P2" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="P2 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P2),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P2))	
		##################################################################################################################################
		IsCreated=False
		x=0
		nbrdevices=1
		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "P3" : "1"}
		Domoticz.Debug("Options to find or set : " + str(Options))
		for x in Devices:
			if Devices[x].Options == Options:
				IsCreated = True
				Domoticz.Log("Devices already exist. Unit=" + str(x))
				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
				nbrdevices=x
			if IsCreated == False :
				nbrdevices=x
		if IsCreated == False and Parameters["Mode4"] == "True":
			nbrdevices=nbrdevices+1
			Domoticz.Device(Name="P3 - " + adr_channel, Unit=nbrdevices, Type=248, Switchtype=0).Create()
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P3),Options = Options)
		elif IsCreated == True :
			Devices[nbrdevices].Update(nValue = 0,sValue = str(P3))	
	
	##############################################################################################################
	#####################################Frame infoType 9		Oregon Rain sensors  ############
	##############################################################################################################
	if infoType == "9":
		protocol = DecData['frame']['header']['protocol']
		id_PHY = DecData['frame']['infos']['id_PHY']
		adr_channel = DecData['frame']['infos']['adr_channel']
		qualifier = DecData['frame']['infos']['qualifier']
		try:
			lowBatt = DecData['frame']['infos']['lowBatt']
		except IndexError:
			lowbatt="0"
		try:
			TotalRain = DecData['frame']['infos']['measures'][0]['value']
		except IndexError:
			TotalRain = "0"
		try :
			CurrentRain = DecData['frame']['infos']['measures'][1]['value']
		except IndexError:
			CurrentRain = "0"

		Domoticz.Debug("id_PHY : " + id_PHY + " adr_channel : " + adr_channel)
		
#		Options = {"infoType":infoType, "id_PHY": str(id_PHY), "adr_channel": str(adr_channel), "protocol": str(protocol), "Temp" : "1"}
#		Domoticz.Debug("Options to find or set : " + str(Options))
#		for x in Devices:
#			if Devices[x].Options == Options:
#				IsCreated = True
#				Domoticz.Log("Devices already exist. Unit=" + str(x))
#				Domoticz.Debug("Options find in DB: " + str(Devices[x].Options) + " for devices unit " + str(x))
#				nbrdevices=x
#			if IsCreated == False :
#				nbrdevices=x
#		if IsCreated == False and Parameters["Mode4"] == "True":
#			nbrdevices=nbrdevices+1
#			Domoticz.Device(Name="Temp - " + adr_channel, Unit=nbrdevices, Type=80, Switchtype=0).Create()
#			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp),Options = Options)
#		elif IsCreated == True :
#			Devices[nbrdevices].Update(nValue = 0,sValue = str(temp))
	
	
	if Parameters["Mode6"] == "Debug":
		writetofile(ReqRcv)
	ReqRcv=""
	return


def SendtoRfplayer(Unit, Command, Level, Hue):
	Options=Devices[Unit].Options
	Domoticz.Debug("SendtoRfplayer - Options find in DB: " + str(Devices[Unit].Options) + " for devices unit " + str(Unit))
	infoType = Options['infoType']
	protocol=Options['protocol']
	if protocol =="1": protocol="X10"
	if protocol =="2": protocol="VISIONIC"
	if protocol =="3": protocol="BLYSS"
	if protocol =="4": protocol="CHACON"
	if protocol =="5": protocol="OREGON"
	if protocol =="6": protocol="DOMIA"
	if protocol =="7": protocol="OWL"
	if protocol =="8": protocol="X2D"
	if protocol =="9": protocol="RTS"
	if protocol =="10": protocol="KD101"
	if protocol =="11": protocol="PARROT"

	if infoType == "0" :
		id=Options['id']
		lineinput='ZIA++' + str(Command.upper()) + " " + protocol + " ID " + id
		Domoticz.Send(bytes(lineinput + '\n\r','utf-8'))
		if Command == "On":
			Devices[Unit].Update(nValue =1,sValue = "on")
		if Command == "Off":
			Devices[Unit].Update(nValue =0,sValue = "off")
	
	if infoType == "1" :
		id=Options['id']
		lineinput='ZIA++' + str(Command.upper()) + " " + protocol + " ID " + id + ""
		Domoticz.Send(bytes(lineinput + '\n\r','utf-8'))
		if Command == "On":
			Devices[Unit].Update(nValue =1,sValue = "on")
		if Command == "Off":
			Devices[Unit].Update(nValue =0,sValue = "off")
	
	return

def writetofile(ReqRcv):
	with open(Parameters["HomeFolder"]+"Response.txt", "at") as text_file:
		print(ReqRcv, file=text_file)
	return

	
def faketest():
	### type 1
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "0", "rfLevel": "-41", "floorNoise": "-97", "rfQuality": "10", "protocol": "3", "protocolMeaning": "BLYSS", "infoType": "1", "frequency": "433920"},"infos": {"subType": "0", "id": "4261483730", "subTypeMeaning": "OFF"}}'
	ReadData(ReqRcv)
	
	### type 2
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "1", "rfLevel": "-50", "floorNoise": "-107", "rfQuality": "10", "protocol": "2", "protocolMeaning": "VISONIC", "infoType": "2", "frequency": "868950"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "1166992416", "qualifier": "8", "qualifierMeaning": { "flags": ["Supervisor/Alive"]}}}} '
	ReadData(ReqRcv)
	### type 2
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "1", "rfLevel": "-52", "floorNoise": "-107", "rfQuality": "10", "protocol": "2", "protocolMeaning": "VISONIC", "infoType": "2", "frequency": "868950"},"infos": {"subType": "0", "subTypeMeaning": "Detector/Sensor", "id": "1166992416", "qualifier": "1", "qualifierMeaning": { "flags": ["Tamper"]}}}} '
	ReadData(ReqRcv)
	### type 4
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-64", "floorNoise": "-106", "rfQuality": "10", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "4", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x1A2D", "id_PHYMeaning": "THGR122/228/238/268,THGN122/123/132", "adr_channel": "47874",  "adr": "187",  "channel": "2",  "qualifier": "33",  "lowBatt": "1", "measures" : [{"type" : "temperature", "value" : "+11.2", "unit" : "Celsius"}, {"type" : "hygrometry", "value" : "52", "unit" : "%"}]}}}'
	ReadData(ReqRcv)
	### type 9
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "0", "rfLevel": "-71", "floorNoise": "-98", "rfQuality": "5", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "9", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x2A19", "id_PHYMeaning": "PCR800", "adr_channel": "39168",  "adr": "153",  "channel": "0",  "qualifier": "48",  "lowBatt": "0", "measures" : [{"type" : "total rain", "value" : "1040.1", "unit" : "mm"}, {"type" : "current rain", "value" : "12.3", "unit" : "mm/h"}]}}} '
	ReadData(ReqRcv)
	### type 6
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "0", "rfLevel": "-64", "floorNoise": "-97", "rfQuality": "6", "protocol": "5", "protocolMeaning": "OREGON", "infoType": "6", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x1A89", "id_PHYMeaning": "WGR800", "adr_channel": "40192",  "adr": "157",  "channel": "0",  "qualifier": "48",  "lowBatt": "0", "measures" : [{"type" : "wind speed", "value" : "5", "unit" : "m/s"}, {"type" : "direction", "value" : "135", "unit" : "degree"}]}}} '
	ReadData(ReqRcv)
	### type 8
	ReqRcv='ZIA33{ "frame" :{"header": {"frameType": "0", "dataFlag": "0", "rfLevel": "-41", "floorNoise": "-97", "rfQuality": "10", "protocol": "7", "protocolMeaning": "OWL", "infoType": "8", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0x0003", "id_PHYMeaning": "CM180i", "adr_channel": "784",  "adr": "49",  "channel": "0",  "qualifier": "6",  "lowBatt": "0", "measures" : [{"type" : "energy", "value" : "47890", "unit" : "Wh"}, {"type" : "power", "value" : "385", "unit" : "W"}, {"type" : "P1", "value" : "325", "unit" : "W"}, {"type" : "P2", "value" : "100", "unit" : "W"}, {"type" : "P3","value" : "190", "unit" : "W"}]}}} '
	ReadData(ReqRcv)
	### type 7
	ReqRcv='ZIA33{"frame" :{"header": {"frameType": "0", "cluster": "0", "dataFlag": "0", "rfLevel": "-84", "floorNoise": "-113", "rfQuality": "2","protocol": "5", "protocolMeaning": "OREGON", "infoType": "7", "frequency": "433920"},"infos": {"subType": "0", "id_PHY": "0xDA78", "id_PHYMeaning": "UVN800","adr_channel": "2054",  "adr": "8",  "channel": "6",  "qualifier": "17","lowBatt": "0","measures" : [{"type" : "UV", "value" : "5", "unit" : "1/10 index"}]}}}'
	ReadData(ReqRcv)