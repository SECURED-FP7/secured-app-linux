#!/usr/bin/python
from gi.repository import NetworkManager as nm, GLib, NMClient
from IWList import *

interface_name = "wlan0"

def getSignal(ssid):
        '''try:
            iwl = IWList(self.interface_name)
            data = iwl.getData()
            for cell in data:
                cellinfo = data[cell]
                if (cellinfo["ESSID"] == ssid):
                    return int(cellinfo["Signal"])
            return None
        except:
            print colored("[Mobility Client]",'red')+": Error in the response from wireless interface."
            return None'''
        try:
            iwl = IWList(interface_name)
            data = iwl.getData()
            for cell in data:
                cellinfo = data[cell]
                if (cellinfo["ESSID"] == ssid):
                    q = cellinfo["Quality"]
                    if q:
                        q = q.split('/')
                        print q[0]
                        print q[1]
                        q = (float(q[0])/float(q[1]))*100
                        print q
                        return q
            return None
        except:
            print "Error in the response from wireless interface."
            return None

nmc = NMClient.Client.new()
devs = nmc.get_devices()

for dev in devs:
    if dev.get_device_type() == nm.DeviceType.WIFI:
            currentAP = dev.get_active_access_point()
            if currentAP:
                print "current AP: \n\t" + currentAP.get_ssid() + "\t" + currentAP.get_bssid()
                currentDevice = dev
                # currentConnection["signal"] = currentAP.get_strength()

                signal = getSignal(currentAP.get_ssid())
                if(signal):
                    print "\tsignal: " + str(signal)
                else:
                    print "NO SIGNAL"



