#!/usr/bin/python
#  We need to install the following packages:
#   python-networkmanager python-gi

from gi.repository import NetworkManager as nm, GLib, NMClient
#import NetworkManager
import json
import requests
import urllib2
import httplib
import threading
import re
import sys
import subprocess
from IWList import *
import socket, struct, netaddr
# import socket, struct
from time import sleep, time
import ConfigParser

def colored(text, color):
    end = '\033[1;m'
    if color == 'green':
        return '\033[1;42m'+text+end
    elif color == 'blue':
        return '\033[1;44m'+text+end
    elif color == 'brown':
        return '\033[1;43m'+text+end
    elif color == 'magenta':
        return '\033[1;45m'+text+end
    elif color == 'grey':
        return '\033[1;47m'+text+end
    elif color == 'cyan':
        return '\033[1;46m'+text+end
    elif color == 'red':
        return '\033[1;41m'+text+end
    elif color == 'yellow':
        return '\033[1;48m'+text+end
    else:
        return text

class MobilityClient:
    def __init__(self, controller):
        self.saved_connections = []
        self.main_loop = GLib.MainLoop()

        #self.controller.config = ConfigParser.RawConfigParser()

        ########################################################
        # Initilizing mobile client's configurations
        ########################################################
        self.psc_ip = controller.config.get('Mobility','psc_ip')
        self.port = controller.config.get('Mobility','port')
        self.psc_mobility_report_uri = "http://{}:{}/mobReport".format(self.psc_ip, self.port)
        self.stop_mobility = False
        self.controller = controller
        self.lock = threading.Lock()
        self.interface_name = controller.config.get('Mobility','interface_name')
        self.interval = float(controller.config.get('Mobility','INTERVAL_BETWEEN_REPORTS'))
        self.interval_migrating = float(controller.config.get('Mobility','INTERVAL_BETWEEN_REPORTS_WHILE_MIGRATING'))
        self.interval_iwlist = float(controller.config.get('Mobility','INTERVAL_BETWEEN_IWLIST_REQUESTS'))

        self.migrating = False
        self.currentConnection = {}
        self.wifilist = []


    def connections_read(self,settings):
        print colored("[Mobility Client]",'green')+": SAVED CONNECTIONS: "
        for c in settings.list_connections():
            bssid = ""
            bssids = []
            if c.get_setting_wireless():
                # if("secured" in c.get_id().lower()):
                num = c.get_setting_wireless().get_num_seen_bssids()
                ssid = c.get_setting_wireless().get_ssid()
                i = 0
                while i < num:
                    bssid = c.get_setting_wireless().get_seen_bssid(i)
                    bssids.append(bssid)
                    i = i + 1
                conObj = {}
                conObj["connection"] = c
                conObj["id"] = c.get_id()
                conObj["bssids"] = bssids
                conObj["ssid"] = ssid
                print "%27s --- %s -- %s" % (c.get_id(), bssids, ssid)
                self.saved_connections.append(conObj)
        self.main_loop.quit()

    def start(self):
        settings = NMClient.RemoteSettings.new(None)
        # wait for connections to be loaded over D-Bus and log
        # them from a callback
        settings.connect("connections-read", self.connections_read)
        self.main_loop.run()
        self.nmc = NMClient.Client.new()
        self.initiliazeConnectionInfo()
        self.reportAPs()
        self.getIWlistSignals()

    def stop_m(self):
        self.stop_mobility = True

    def getIWlistSignals(self):
        print colored("[IWList Request]",'yellow')+": Starting IWList request"
        nmc = self.nmc
        devs = nmc.get_devices()
        wl = []
        connection = ""
        APs = []
        try:
            ssids_list = open("ssids_list").read()
        except Exception as e:
            print colored("[IWList Request]", 'yellow')+": Couldn't read ssids list file"
            return
        print("IWLIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIST")
        for dev in devs:
            if dev.get_device_type() == nm.DeviceType.WIFI:
                    currentAP = dev.get_active_access_point()
                    if currentAP:
                        self.currentConnection["bssid"] = currentAP.get_bssid()
                        self.currentConnection["ssid"] = currentAP.get_ssid()
                        currentDevice = dev
                        allSignals = False

                        while not allSignals:
                            allSignals = True
                            for ap in dev.get_access_points():
                                #print colored("[IWList Request]",'yellow')+": LOOKING: " + ap.get_ssid()
                                if allSignals and ap.get_ssid() != "":

                                    b = ap.get_ssid() in ssids_list

                                    if b and (ap.get_ssid().lower() not in APs):

                                        signal = self.getSignal(ap.get_ssid())
                                        if (signal):
                                            print colored("[IWList Request]",'yellow')+": Getting signal from: " + ap.get_ssid()
                                            print colored("[IWList Request]",'yellow')+": Signal: " + str(signal)
                                            wifijson = {"ssid": ap.get_ssid(), "signal": signal, "bssid": ap.get_bssid()}
                                            # wifijson["signal"] = ap.get_strength()
                                            wl.append(wifijson)
                                            APs.append(ap.get_ssid().lower())
                                        else:
                                            #print colored("[IWList Request]",'yellow')+": NO SIGNAL FOUND "
                                            allSignals = False
                        self.wifilist = wl
        if not self.stop_mobility:
            threading.Timer(self.interval_iwlist, self.getIWlistSignals).start()


    def getSignal(self,ssid):
        try:
            iwl = IWList(self.interface_name)
            data = iwl.getData()
            for cell in data:
                cellinfo = data[cell]
                if (cellinfo["ESSID"] == ssid):
                    q = cellinfo["Quality"]
                    if q:
                        q = q.split('/')
                        q = (float(q[0]) / float(q[1])) * 100
                        return q
            return None
        except Exception,e:
            print colored("[Mobility Client]", 'red') + ": Error in the response from wireless interface."

            print colored("[Mobility Client]", 'red') + ": ERROR: " + str(e)
            return None

    def search_saved_connection(self,bssid, ssid):
        for obj in self.saved_connections:
            if bssid:
                if bssid in obj["bssids"]:
                    return obj["connection"]
            if (str(ssid).strip() == str(obj["ssid"]).strip()) or (str(ssid).strip() is str(obj["ssid"]).strip()):
                if ssid in obj["ssid"]:
                    return obj["connection"]
        return None





    def getIP(self, dev):
    ############################################
    #   Returns the IP of the client. We only return an IP if it is
    #   different from the one currently dsiplyed since this method
    #   should be invoked only in the case of a handover or the
    #   application's boot-up. If the IP is the same or the Netwrok
    #   Manager did not return a valid response it returns -1.
    ############################################
        try:
            addresses = []
            for address in dev.get_ip4_config().get_addresses():
                ip_address = address.get_address()
                addr = '.'.join(str(netaddr.IPAddress(ip_address)).split('.')[::-1])
                addresses.append(addr)

            addresses = ' '.join(addresses)
            print colored("[Conection INFO]",'green')+": Addresses:",str(addresses)
            if self.controller.ui.wifiIP.text() == addresses:
                return '-1'
            return addresses
        except Exception, e:
            print colored("[Conection INFO]",'red')+": ERROR in getting new IP information"
            print colored("[Conection INFO]",'red')+": ERROR: ",str(e)
            return '-1'

    def updateConnectionInformation(self,dev,apName):
        ############################################
        # We only update connection information if indeed the access point has
        # changed so we don't block the main Qt thread if no actual new information
        # is present.
        ############################################
        print("hi: " + str(self.controller.currentAP))
        if self.controller.currentAP == None or self.controller.currentAP != apName :
            if dev.get_device_type() == nm.DeviceType.WIFI:
                connType = 'Wi-Fi'
            elif dev.get_device_type() == nm.DeviceType.ETHERNET:
                connType = 'Ethernet'

            ####################
            # Attempting to retrieve the IP. In case of handover we make 10 attempts
            # to read the new IP of the client. Before each attempt we wait a 1 second.
            # If we don't get a new IP we default to an empty string.
            ####################
            for i in range(10):
                print colored("[Conection INFO]",'green')+": Trying to get new IP information. Attempt: ",str(i)
                addresses = self.getIP(dev)
                if addresses != '-1':
                    break
                print colored("[Conection INFO]",'green')+": Waiting 1 second to try again."
                sleep(1)

            if addresses == '-1':
                print colored("[Conection INFO]",'red')+": Did not get new IP information. Setting IP information to empty."
                addresses = ''
            print("before setApIp: "+apName)
            self.controller.setApIp(apName, addresses)
            #self.controller.currentAP = apName
            #self.controller.IP = addresses
            self.controller.callUpdateConnectionInfoView()

    def initiliazeConnectionInfo(self):
        try:
            devs = self.nmc.get_devices()
            for dev in devs:
                if dev.get_device_type() == nm.DeviceType.WIFI:
                        currentAP = dev.get_active_access_point()
                        if currentAP:
                            self.updateConnectionInformation(dev,currentAP.get_ssid())
                            break
            print colored("[Mobility Client]",'green')+": Initialized the connection information."
        except Exception, e:
            print colored("[Mobility Client]",'red')+": Error initializing the connection information."
            print colored("[Mobility Client]",'red')+": Error: ",str(e)



    def getCurrentAP(self):
        ######################################################
        #   Static method used by client_sec.py to get the access point method
        #   to initiate the IPSec tunnel if USE_MOBILITY is true.
        #   In the mobility scenario we follow the convention that the name
        #   of the IPsec connection in ipsec.conf must be the same as the access
        #   point's SSID.
        ######################################################
        print colored("[Mobility Client]",'grey')+": Getting current Access Point."
        try:
            nmc = NMClient.Client.new()
            for dev in nmc.get_devices():
                if dev.get_device_type() == nm.DeviceType.WIFI:
                    currentAP = dev.get_active_access_point()
                    if currentAP:
                        ssid = currentAP.get_ssid()
                        self.updateConnectionInformation(dev,ssid)
                        print colored("[Mobility Client]",'grey')+": Current Access Point:",ssid
                        return
        except Exception, e:
            print colored("[Mobility Client]",'red')+": Error in getting Access Point: ",str(e)
            return
        print colored("[Mobility Client]",'grey')+": Access Point not found"
        return


    def reportAPs(self):
        try:
            #print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Starting"
            send = len(self.wifilist) > 0

            print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"] Send:",str(send)
            if (send is True) and (not self.stop_mobility) and (not self.lock.locked()):
                self.lock.acquire()
                try:
                    allow = "no"
                    if self.controller.allowHandover:
                        allow = "yes"
                    reportJson = {"currentConnection": self.currentConnection, "ap-list": self.wifilist, "user": self.controller.user, "allowHandover": allow}
                    report = json.dumps(reportJson)
                    print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Sending Message to PSC"
                    print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Current Connection: ",self.currentConnection
                    print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Wi-Fi List: "
                    for w in self.wifilist:
                        print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: " + str(w["ssid"]) + ": " + str(w["signal"])

                    try:

                        response = requests.put(self.psc_mobility_report_uri, data=report)
                        response = json.loads(response.content)
                    except:
                        response = {'action':-1, 'error':'PSC not reachable yet.'}

                    print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Response from PSC:",response

                    if response["action"] == 0:
                        print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: OK. Hand Over not needed"
                    elif response["action"] == 1:
                        self.controller.updateStatus(2)
                        print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: Migration on progress... Waiting for the handover order"

                        self.migrating = True
                    elif response["action"] == 2:
                        print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: Hand Over needed. Changing connection to access point: " + response["bssid"]

                        nmc = self.nmc
                        devs = nmc.get_devices()
                        for dev in devs:
                            if dev.get_device_type() == nm.DeviceType.WIFI:
                                for ap in dev.get_access_points():
                                    if ap.get_bssid() == response["bssid"]:
                                        print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: IPSEC disconnecting from " + self.controller.active_ipsec_connection
                                        self.controller.closeIPsecConnection()
                                        newSsid = ap.get_ssid()
                                        print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: Access point found: %s. Searching it on the saved connections." % newSsid
                                        connection = self.search_saved_connection(ap.get_bssid(), ap.get_ssid())
                                        if connection:
                                            print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: AP Found. Trying to connect."
                                            nmc.activate_connection(connection, dev, ap.get_path(), None, None)
                                        else:
                                            print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: AP Not Found. Adding it and trying to connect."
                                            nmc.add_and_activate_connection(None, dev, ap.get_path(), None, None)

                                        connName = self.controller.getIpsecConnectionFromSsid(newSsid)
                                        print colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: IPSEC Connecting to " + connName
                                        sleep(4)
                                        self.controller.makeIPsecConnection(connName)

                                        self.updateConnectionInformation(dev,newSsid)
                                        self.controller.updateStatus(1)
                                        print  colored("[Mobility Client:Handover]",'cyan')+":["+str(threading.current_thread().name)+"]: SUCCESS"



                    else:
                        print colored("[Mobility Client]",'red')+":["+str(threading.current_thread().name)+"]: ERROR: " + response["error"]
                except Exception,e:
                    print colored("[Mobility Client]",'red')+":["+str(threading.current_thread().name)+"]: ERROR updating the connection information"
                    print colored("[Mobility Client]",'red')+":["+str(threading.current_thread().name)+"]: ERROR: ",str(e)
                finally:
                    self.lock.release()
            #print colored("[Mobility Client]",'green')+":["+str(threading.current_thread().name)+"]: Exiting"
        finally:
            if self.migrating:
                threading.Timer(self.interval_migrating, self.reportAPs).start()
            elif not self.stop_mobility:
                threading.Timer(self.interval, self.reportAPs).start()
            return

if __name__ == "__main__":
    nmc = NMClient.Client.new()
    reportAPs()
