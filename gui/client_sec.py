# -*- coding: latin1 -*-
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4 import uic

#from GUI import Ui_GUI

from ui_authenticateDialog import Ui_AuthenticateDialog
import threading
from time import sleep, time
import time
import webbrowser
import os
import subprocess
import json
import hashlib
import requests
import json
import PyQt4.QtGui
from PyQt4.QtGui import *
import ConfigParser
from MobilityClient import MobilityClient
import logging
import ast

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
    else:
        return text

class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))


    
class GUI(QMainWindow):
    authenticateSignal = QtCore.pyqtSignal()
    updateConnectionInfoSignal = QtCore.pyqtSignal()
    updatetIpsecConnectionInfoSignal = QtCore.pyqtSignal()

    def normalOutputWritten(self, text):
        cursor = self.console.logWindow.textCursor()
        cursor.movePosition(PyQt4.QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.console.logWindow.setTextCursor(cursor)
        self.console.logWindow.ensureCursorVisible()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent) 
        self.appName = "SECURED App"

        pix = QPixmap(800, 600)
        pix.fill(Qt.black)
        self.splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
        self.splash.showMessage("Loading "+self.appName+"...", Qt.AlignCenter, Qt.white)
        self.splash.show();
        qApp.processEvents()

        self.ui = uic.loadUi("GUI.ui",self)
        self.ui.show()

        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.read('gui.conf')
            print colored("[Configuration]",'grey')+": Loaded Configuration"  
        except:
            print colored("[Configuration]",'grey')+": Cannot read the configuration file"
            return     

        # MOBILITY RELATED
        # ==============
        # 
        self.useMobility = self.config.getboolean('Mobility','USE_MOBILITY')
        self.allowHandover = True
        self.NED_URL = self.config.get('NED','NED_URL')
        
        self.initializeView()
        #self.console = uic.loadUi("console.ui",self)
        #self.console.show()

        self.authWindow = None
        
        self.dialog = AuthenticateDialog("", self)
        self.dialog.setModal(True)
        self.dialog.hide()
        
        self.splash.finish(self)
        
        self.psanames = {'dansguardian':'Content Filter', 'squid':'Application Layer Filter', 'iptables':'Packet Filter', 'iptablespsa':'Packet Filter', 'anonimityvpn':'Anonymity', 'antiphishingpsa':'Anti-Phishing', 'bandwidthcontrol':'Bandwidth Control', 'brologging':'Network Monitor (Bro)', 'bromalware':'Anti-Malware (Bro)', 'reencryptpsa':'Web proxy re-encrypt', 'strongswan':'Privacy (VPN)'}


        # IPSEC RELATED
        # ==============
        # BELOW determines the timeout (seconds) when we check verifier's attestation status with a POST
        self.ATTESTATION_TIME = self.config.getint('IPSEC','ATTESTATION_TIME')
        self.IPSEC_NED_CONNECTION_NAME = self.config.get('IPSEC','IPSEC_NED_CONNECTION_NAME')
        
        self.DIR_TO_RUN_IPSEC_COMMANDS= self.config.get('IPSEC','DIR_TO_RUN_IPSEC_COMMANDS')
        self.IPSEC_START_CMDS = self.DIR_TO_RUN_IPSEC_COMMANDS + "/"+self.config.get('IPSEC','IPSEC_START_CMDS')
        self.IPSEC_STOP_CMDS = self.DIR_TO_RUN_IPSEC_COMMANDS + "/"+self.config.get('IPSEC','IPSEC_STOP_CMDS')            

        # VERIFIER RELATED
        # ==============
        self.NED_ID = self.config.get('NED','NED_ID')
        self.GGUI_URL = self.config.get('NED','GGUI_URL')
        self.VERIFIER_URL = self.config.get('VERIFIER','VERIFIER_URL')
        self.INTEGRITY_LVL_NUMBER = self.config.getint('VERIFIER','INTEGRITY_LVL_NUMBER')
        self.INTEGRITYLEVEL1 = self.config.get('VERIFIER','INTEGRITYLEVEL1')
        self.INTEGRITYLEVEL2 = self.config.get('VERIFIER','INTEGRITYLEVEL2')
        self.INTEGRITYLEVEL4 = self.config.get('VERIFIER','INTEGRITYLEVEL4')
        self.VERIFIER_WEB_URL = self.config.get('VERIFIER','VERIFIER_WEB_URL')
            
        self.USED_INTEGRITY = self.INTEGRITYLEVEL4           

        # GUI COMPONENT RELATED
        # ==============
        # If SHOW_WARNING_DIALOG == False, then user is not prompted about untrusted ned
        # then the user only sees the text warning, no dialog!
        self.SHOW_WARNING_DIALOG = True
        # We only show the warning dialog once, if this is set to True 
        self.attestation_warning_shown = True
        
        self.currentAP = None
        self.status = None
        self.user = None
        self.setUserLoggedIn(None)
        
        self.SHOW_LOGGED_IN_USER = True
        self.status = True
        self.mobClient = MobilityClient(self)
        
        # If no mobility, use defaultNED
        if not self.useMobility:
            self.currentAP = self.NED_ID

        self.active_ipsec_connection = None
        
        self.updateStatus(0)
        
        # Add signal from MobilityClient to update gui image of connection
        self.updateConnectionInfoSignal.connect(self.updateConnectionInfoView)
        self.updatetIpsecConnectionInfoSignal.connect(self.setIpsecConnectionInfo)
        
        # Threads for logging in and attestation
        self.loginPageAvailableTask = LoginAvailableTaskThread(self.NED_URL)
        self.loginPageAvailableTask.requestTaskFinished.connect(self.onNedConnectionAvailable)
        self.requestTask = RequestTaskThread(self.NED_URL)
        self.requestTask.requestTaskFinished.connect(self.onLogin)
        # Everything related to attestation is done within self.attestationTask
        
        self.attestationTask = AttestationRequestThread(self.config)
        self.attestationTask.currentAP = self.currentAP
        self.attestationTask.requestTaskFinished.connect(self.onAttestation)

        #Creating Poll PSC task
        self.pscCommunicationTask = PSCCommunicationThread()
        self.connect(self.pscCommunicationTask, SIGNAL("event_psa_list(QString)"), self.onPsaList)
        
        # Actions triggered from File-> menu
        self.ui.actionLogin.triggered.connect(self.loginAction)
        self.ui.actionLogout.triggered.connect(self.logoutAction)

        self.ui.startMobilityButton.clicked.connect(self.pressedStartMobilityButton)
        self.ui.stopMobilityButton.clicked.connect(self.pressedStopMobilityButton)
        self.ui.startHandoverButton.clicked.connect(self.pressedStartHandoverButton)
        self.ui.stopHandoverButton.clicked.connect(self.pressedStopHandoverButton)
        # Add connections to buttons clicked (login/logout, show attest result, GGUI)
        self.ui.policyButton.clicked.connect(self.openPolicyGui)
        self.ui.nedStatusButton.clicked.connect(self.openNedStatus)
        self.ui.loginButton.clicked.connect(self.loginAction)
        self.ui.logoutButton.clicked.connect(self.logoutAction)

        self.mobClient.getCurrentAP()
        
        # We connect directly to IPsec and start checking when the login page is available
        # Then the authentiction dialog is shown to the user. The user can also use menu to authenticate.
        if self.currentAP:
            try:
                if self.useMobility:
                    connName = self.getIpsecConnectionFromSsid(self.currentAP)
                    if connName:
                        self.makeIPsecConnection(connName)
                else:
                    # If mobility not used, first start attestation request, after attest
                    # start IPSEC to the trusted NED.
                    # Should we attest immediately
                    self.attestationTask.start()

            except Exception, e:
                res = QMessageBox.critical(self, "An error occurred", "The system could not establish a secure and trusted channel. Please check your configuration and try again.", QMessageBox.Ok)
                print colored("[IPsec]",'red')+": ERROR Getting IPsec connection name."
                print colored("[IPsec]",'red')+": "+ str(e)
                return
        else:
            res = QMessageBox.critical(self, "An error occurred", "You are not connected to any access point. Please try again once you are connected to one of our wifi access points.", QMessageBox.Ok)
            print colored("[IPsec]",'red')+": ERROR Getting Current AP."
            print colored("[IPsec]",'red')+"current ap not available"
            return
        
        self.connect(self.ui.listWidget,
             QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"),
             self.psaDoubleClicked)

        # Start testing whether user can login
        self.loginPageAvailableTask.start()

	    # Create PSA event thread, if required later, now only one PSA for event monitoring
        self.psaEventThread = PsaEventThread("BroMalware")
        self.connect(self.psaEventThread, SIGNAL("add_event(QString, QString)"), self.add_event)

	    # Start attestation to see attestation before login
        self.attestationTask.start()


    def add_event(self, psa, msg):
        print "ADD event: from:" + psa +", msg:" + msg
        self.showPsaCritical(psa, msg)

    def enableMonitoring(self, psa):
        self.psaEventThread.start()

    def stopPsaEventThread(self):
        self.psaEventThread.stopThis()

    def showPsaCritical(self, psa, msg):
        QMessageBox.critical(self, "Message from " + psa, msg, QMessageBox.Ok)
        # Bring app to front to notify user
        self.activateWindow()


    def updateStatus(self,status):
        if status == 0:
            self.ui.statusLabel.setText('<b><font color="red">Not enforced</font></b>')
        elif status == 1:
            self.ui.statusLabel.setText('<b><font color="green">Enforced</font></b>')
        else :
            self.ui.statusLabel.setText('<b><font color="blue">Migrating...</font></b>')
        

    # FUNCTIONS CALLED FROM MobilityClient!
    ##
    def setApIp(self, currentAP, ip):
        """
        Called from MobilityClient.
        """
        self.currentAP = currentAP
        self.IP = ip
        self.attestationTask.currentAP = currentAP

    def callUpdateConnectionInfoView(self):
        self.updateConnectionInfoSignal.emit()

    def callUpdatetIpsecConnectionInfo(self):
        self.updatetIpsecConnectionInfoSignal.emit()
        
    def updateConnectionInfoView(self):
        try:
            if(self.currentAP):
                self.ui.logo_5.setVisible(True)
                self.wifiName.setText('<b><font color="blue">%s</font></b>' % self.currentAP)
                self.wifiName.setVisible(True)
            
                if self.IP:
                    self.ui.wifiIP.setText(self.IP)
                    self.ui.wifiIP.setVisible(True)
                else:
                    self.controller.ui.wifiIP.setVisible(False)                
                print colored("[Conection INFO]",'green')+": Updated connection information"
                print colored("[Conection INFO]",'green')+": Name: %s IP: %s" % (self.currentAP,self.IP)
        except Exception, e:
            print colored("[Conection INFO]",'red')+": ERROR in updating connection information"
            print colored("[Conection INFO]",'red')+": ERROR: ",str(e)

    # END FUNCTIONS CALLED FROM MobilityClient
    #-------------


    def initializeView(self):
        w = self.ui
        '''p = w.palette()
        p.setColor(w.backgroundRole(), PyQt4.QtGui.QColor("#FFFFFF"))
        w.setPalette(p)'''
        
        self.ui.wifiName.setText("Getting current wifi...")
        self.ui.wifiIP.setVisible(False)
        self.ui.attestationTime.setVisible(False)
        #self.ui.verifier_link.setVisible(False)
        self.ui.noTrustedNedIcon.setVisible(False)
        self.ui.trustedNedIcon.setVisible(False)
        self.ui.lastUpdateLabel.setVisible(False)
        self.ui.timeIcon.setVisible(False)
        #self.ui.infoIcon.setVisible(False)
        self.ui.logoutButton.setVisible(False)

        if self.useMobility:
            self.ui.mobilityStatusOff.setVisible(False)
            self.ui.handoverStatusOff.setVisible(False)
            self.ui.startMobilityButton.setVisible(False)
            self.ui.startHandoverButton.setVisible(False)
        else:            
            self.ui.mobilityStatusOff.setVisible(True)
            self.ui.mobilityStatusOn.setVisible(False)
            self.ui.startMobilityButton.setVisible(True)
            self.ui.stopMobilityButton.setVisible(False)
            self.ui.handoverStatusOff.setVisible(False)
            self.ui.handoverStatusOn.setVisible(False)
            self.ui.startHandoverButton.setVisible(False)
            self.ui.stopHandoverButton.setVisible(False)
            self.ui.handoverStatusLabel.setVisible(False)
            self.ui.mobilityStatusLabel.setText("<b>Mobility Off</b>")

            # Hide AP icon if no mobility
            self.ui.logo_5.setVisible(False)
            self.ui.wifiName.setVisible(False)
            # Also hide mobile buttons if no mobility
            self.ui.mobilityStatusOff.setVisible(False)
            self.ui.handoverStatusOff.setVisible(False)
            self.ui.startMobilityButton.setVisible(False)
            self.ui.startHandoverButton.setVisible(False)
        
    def pressedStartMobilityButton(self):
        self.ui.mobilityStatusOff.setVisible(False)
        self.ui.mobilityStatusOn.setVisible(True)
        self.ui.startMobilityButton.setVisible(False)
        self.ui.stopMobilityButton.setVisible(True)
        self.ui.handoverStatusOff.setVisible(False)
        self.ui.handoverStatusOn.setVisible(True)
        self.ui.startHandoverButton.setVisible(False)
        self.ui.stopHandoverButton.setVisible(True)
        self.ui.handoverStatusLabel.setVisible(True)
        self.ui.mobilityStatusLabel.setText("<b>Mobility On</b>")
        self.ui.handoverStatusLabel.setText("<b>Handover On</b>")
        self.useMobility = True
        self.startMobilityScript()

    def pressedStopMobilityButton(self):
        self.ui.mobilityStatusOff.setVisible(True)
        self.ui.mobilityStatusOn.setVisible(False)
        self.ui.startMobilityButton.setVisible(True)
        self.ui.stopMobilityButton.setVisible(False)
        self.ui.handoverStatusOff.setVisible(False)
        self.ui.handoverStatusOn.setVisible(False)
        self.ui.startHandoverButton.setVisible(False)
        self.ui.stopHandoverButton.setVisible(False)
        self.ui.handoverStatusLabel.setVisible(False)
        self.ui.mobilityStatusLabel.setText("Mobility Off")
        self.useMobility = False
        self.stopMobilityScript()

    def pressedStartHandoverButton(self):
        self.ui.handoverStatusOff.setVisible(False)
        self.ui.handoverStatusOn.setVisible(True)
        self.ui.startHandoverButton.setVisible(False)
        self.ui.stopHandoverButton.setVisible(True)
        self.ui.handoverStatusLabel.setText("Handover On")
        self.allowHandover = True

    def pressedStopHandoverButton(self):
        self.ui.handoverStatusOff.setVisible(True)
        self.ui.handoverStatusOn.setVisible(False)
        self.ui.startHandoverButton.setVisible(True)
        self.ui.stopHandoverButton.setVisible(False)
        self.ui.handoverStatusLabel.setText("Handover Off")
        self.allowHandover = False
            
    def startMobilityScript(self):
        print colored("[Mobility Client]",'green')+": Starting Mobility Script"
        os.chdir(self.DIR_TO_RUN_IPSEC_COMMANDS)
        try:
            self.mobClient.start()
        except Exception, e:
            print e
        print colored("[Mobility Client]",'green')+": Started Mobility Script"

    def stopMobilityScript(self):
        print colored("[Mobility Client]",'green')+": Stopping Mobility Script"
        try:
            self.mobClient.stop_m()
        except Exception, e:
            print e

    def closeEvent(self, event):
        result = QMessageBox.question(self, "Confirm Exit.", "Are you sure you want to exit ?", QMessageBox.Yes| QMessageBox.No)
        if result == QMessageBox.Yes:
            self.logout(False)
            self.stopThreads()
            self.closeIPsecConnection()
            print "closeIPsecConnection done!"
            event.accept()
        else:   
            event.ignore()
        
    # ACTIONS FROM UI
    def loginAction(self):
        print colored("[Login]",'grey')+": loginAction"
        self.showAuthenticateDialog()
        
    def logoutAction(self):
        print colored("[Logout]",'grey')+": logoutAction"
        self.logout()
    
    def openNedStatus(self):
        webbrowser.open(self.VERIFIER_WEB_URL)

    def openPolicyGui(self):
        webbrowser.open(self.GGUI_URL)

    def psaDoubleClicked(self, item):
        print "psaDoubleClicked"
        psa_id = item.data(Qt.UserRole).toPyObject()
        webbrowser.open('http://10.2.2.251:8080/psa/get-log-psa/' + psa_id)

    def setUserLoggedIn(self, user):
        _fromUtf8 = PyQt4.QtCore.QString.fromUtf8
        self.user = user
        if self.user != None:
            self.ui.loginlabel.setText(self.user)
            myPixmap = PyQt4.QtGui.QPixmap(_fromUtf8('images/user.png'))
            self.ui.userIcon.setPixmap(myPixmap)
            self.ui.loginButton.setVisible(False)
            self.ui.logoutButton.setVisible(True)
        else:
            self.ui.loginlabel.setText("Not logged in")
            myPixmap = PyQt4.QtGui.QPixmap(_fromUtf8('images/user_off.png'))
            self.ui.userIcon.setPixmap(myPixmap)
            self.ui.loginButton.setVisible(True)
            self.ui.logoutButton.setVisible(False)

    def initPsaList(self):
        self.ui.listWidget.clear()
        self.ui.listWidget.addItem('Contacting your NED.')

    def updatePsaList(self, psa_str):
        r = ""
        try:
            r = json.loads(str(psa_str))
        except Exception, e:
            print e

        if len(r) == 0:
            print "# updatePsaList: No list found"
            return

        self.ui.listWidget.clear()
        
        for psa in ast.literal_eval(r[u'psa_response']):
            item = PyQt4.QtGui.QListWidgetItem()
            try:
                name = self.psanames[psa[u'id'].lower()]
            except KeyError:
                name =  psa[u'id']
            item.setText('Type: '+name)
            item.setTextColor(PyQt4.QtGui.QColor(0, 102, 0))

            if name == 'Content Filter' or name is 'Content Filter':
                    item.setIcon(PyQt4.QtGui.QIcon(r"cf.jpg"))
            elif name == 'Application Layer Filter' or name is 'Application Layer Filter':
                    item.setIcon(PyQt4.QtGui.QIcon(r"parental_control.png"))
            elif name == 'Packet Filter' or name is 'Packet Filter':
                    item.setIcon(PyQt4.QtGui.QIcon(r"firewall"))
            elif name == 'Anonymity' or name is 'Anonymity':
                    item.setIcon(PyQt4.QtGui.QIcon(r"anon.png"))
            elif name == 'Anti-Phishing' or name is 'Anti-Phishing':
                    item.setIcon(PyQt4.QtGui.QIcon(r"parental_control.png"))
            elif name == 'Bandwidth Control' or name is 'Bandwidth Control':
                    item.setIcon(PyQt4.QtGui.QIcon(r"bw.jpeg"))
            elif name == 'Network Monitor (Bro)' or name is 'Network Monitor (Bro)':
                    item.setIcon(PyQt4.QtGui.QIcon(r"bro.png"))
            elif name == 'Anti-Malware (Bro)' or name is 'Anti-Malware (Bro)':
                    item.setIcon(PyQt4.QtGui.QIcon(r"bro.png"))
            elif name == 'Web proxy re-encrypt' or name is 'Web proxy re-encrypt':
                    item.setIcon(PyQt4.QtGui.QIcon(r"reencrypt.png"))
            elif name == 'Privacy (VPN)' or name is 'Privacy (VPN)':
                    item.setIcon(PyQt4.QtGui.QIcon(r"encrypt.png"))
    
            #set PSA ID
            data = (psa[u'id'])
            item.setData(Qt.UserRole, data)
            self.ui.listWidget.addItem(item)
            if data == 'BroMalware':
                self.enableMonitoring(data)
            print data
    
    def setAttestationStatus(self, result):
        validate_time = self.attestationTask.validate_time
        text = ""
        if result:
            text = '<b><font color="green">%s</font></b>' % "The NED is trusted"
            self.ui.trustedNedIcon.setVisible(True)
            self.ui.noTrustedNedIcon.setVisible(False)
        else:
            text = '<b><font color="red">%s</font></b>' % "The NED is not trusted"
            self.ui.trustedNedIcon.setVisible(False)
            self.ui.noTrustedNedIcon.setVisible(True)
       
        if validate_time != None:
            text_time = str(validate_time)
        
        self.ui.attestationStatus.setText(text)
        self.ui.attestationTime.setText(text_time)
        self.ui.attestationTime.setVisible(True)
        #self.ui.verifier_link.setVisible(True)
        self.ui.lastUpdateLabel.setVisible(True)
        self.ui.timeIcon.setVisible(True)
        #self.ui.infoIcon.setVisible(True)
     
    def showAttestationResult(self, result):
        #print colored("[Attestation]",'blue')+": Attestation Result:" + str(result)
        #QMessageBox.information(self, "Attestation result", result, QMessageBox.Ok)
        self.setAttestationStatus(result)
        
        if self.SHOW_WARNING_DIALOG:
            if result == False and self.attestation_warning_shown == False:
                self.attestation_warning_shown = True
                result = QMessageBox.critical(self, "Warning", 'The NED is not trusted! You should disconnect as soon as possible!',QMessageBox.Yes| QMessageBox.No)
                if result == QMessageBox.Yes:
                        self.logout(False)
                        self.closeIPsecConnection()
                        QApplication.quit()

    def onPsaList(self, str_psa_list):
        """
        Received PSA list from thread on a signal
        """
        a = str(str_psa_list).replace('\\',r'\\')
        self.updatePsaList(str_psa_list)
        
    # Finish attestation task
    def onAttestation(self):
        if self.attestationTask.trusted == False:
            self.showAttestationResult(False)
        elif self.attestationTask.trusted == True:
            self.showAttestationResult(True)
        else:
            print colored("[Attestation]",'red')+":Didn't receive valid trusted/untrusted response this time, issuing another req."
            
        # If mobility not used, make ipsec after attestation result
        if not self.useMobility and self.active_ipsec_connection == None:
            print "Received attestation and creating IPSEC to:" + self.IPSEC_NED_CONNECTION_NAME
            self.makeIPsecConnection(self.IPSEC_NED_CONNECTION_NAME)

    
    # Finish login task
    def onLogin(self):
        self.handleLoginStatus()
    
    # Start login task
    def onNedConnectionAvailable(self):
        time.sleep(0.1)
        if self.loginPageAvailableTask.status == True:
            self.showAuthenticateDialog()
        else:
            #print "login page not available yet.."
            self.loginPageAvailableTask.start()
        
    def showAuthenticateDialog(self):
        self.dialog.show()

    def makeIPsecConnection(self, connName):
        print colored("[IPsec]",'magenta')+": Initiating IPsec Connection."
        os.chdir(self.DIR_TO_RUN_IPSEC_COMMANDS)
        try:            
            print colored("[IPsec]",'magenta')+": Using: " + self.IPSEC_START_CMDS + ' ' + connName
            subprocess.call([self.IPSEC_START_CMDS, connName])
            self.IPSEC_NED_CONNECTION_NAME = connName
            time.sleep(0.5)
        except Exception, e:
            res = QMessageBox.critical(self, "An error occurred", "The system could not establish a secure and trusted channel. Please check your configuration and try again.", QMessageBox.Ok)
            print colored("[IPsec]",'red')+": ERROR in creating IPsec Connection."
            print colored("[IPsec]",'red')+":"+ str(e)
            return
        self.active_ipsec_connection = connName
        self.callUpdatetIpsecConnectionInfo()
        
        print colored("[IPsec]",'magenta')+": Created IPsec Connection."

    def setIpsecConnectionInfo(self):
        if(self.active_ipsec_connection):
            self.ui.connectingTunnelLabel.setVisible(False)
            self.ui.progressBar.setVisible(False)
            _fromUtf8 = PyQt4.QtCore.QString.fromUtf8
            myPixmap = PyQt4.QtGui.QPixmap(_fromUtf8('images/secured_tunnel_sec.png'))
            self.ui.schema_tunnel.setPixmap(myPixmap)
        else:
            self.ui.connectingTunnelLabel.setVisible(False)
            self.ui.progressBar.setVisible(False)
            _fromUtf8 = PyQt4.QtCore.QString.fromUtf8
            myPixmap = PyQt4.QtGui.QPixmap(_fromUtf8('images/secured_tunnel_sec_off.png'))
            self.ui.schema_tunnel.setPixmap(myPixmap)

    def getIpsecConnectionFromSsid(self,ssid):
        print "getIpsecConnectionFromSsid"
        try:
            return self.config.get('Mobility',ssid)
        except Exception,e:
            res = QMessageBox.critical(self, "An error occurred", "Does not exist any entry for the " + str(self.currentAP)  + " access point in the configuration. Please check your configuration or connect to one of our wifi connections and try again.", QMessageBox.Ok)
            print colored("[IPsec]",'red')+":"+ str(e)
            return None


    def closeIPsecConnection(self):
        print colored("[IPsec]",'magenta')+": Closing IPsec Connection"
        try:
            print colored("[IPsec]",'magenta')+": Using: " + self.IPSEC_STOP_CMDS + ' '+self.IPSEC_NED_CONNECTION_NAME
            subprocess.Popen([self.IPSEC_STOP_CMDS, self.IPSEC_NED_CONNECTION_NAME])
        except Exception, e:
            QMessageBox.critical(self, "An error occurred", "The system could not close the secure and trusted channel. Please check your configuration and try again.", QMessageBox.Ok)
            print colored("[IPsec]",'red')+": ERROR in closing IPsec Connection."
            print colored("[IPsec]",'red')+":"+ str(e)
            return
        self.active_ipsec_connection = None
        self.callUpdatetIpsecConnectionInfo()

    def handleLoginStatus(self):
        # Timeout or other exception
        if self.requestTask.r == None:
            res = QMessageBox.information(self, "An error occurred", "There was a problem, please re-authenticate.", QMessageBox.Ok)
            self.showAuthenticateDialog()
            return
        
        status = False
        print colored("[Login]",'grey')+": login reply status:" + str(self.requestTask.r.status_code)
        if self.requestTask.r.status_code == 200:
            print colored("[Login]",'grey')+": login OK"

            # Enable another attestation warning if logged in
            self.attestation_warning_shown = False
            status = True
            self.setUserLoggedIn(self.requestTask.user)
            self.updateStatus(1)
            self.initPsaList()
            # Start attestation
            self.attestationTask.start()
            self.pscCommunicationTask.start()
            if self.useMobility:
                self.startMobilityScript()
        else:
            print colored("[Login]",'red')+": login not OK"
        
        if status == False:
            res = QMessageBox.warning(self, "Login failure", "Please try again.", QMessageBox.Ok)
            self.showAuthenticateDialog()            
            self.setUserLoggedIn(None)
        self.status = status
            
    def stopThreads(self):
        print "stopThreads()"
        self.attestationTask.stop()
        self.stopMobilityScript()
        print "stopThreads() done"

    def logout(self, showMessage = True):
        url = self.NED_URL + "login"
        r = None
        if self.status:
            try:
                r = requests.delete(url, headers={'Content-Type':'application/json'}, timeout=2.000)
            except Exception, e:
                print e
                if r is not None:
                    print colored("[Logout]",'red')+": Status Code: ",r.status_code
                else:    
                    print colored("[Logout]",'red')+": Status Code: ",r
        if r != None and r.status_code == 200:
            print colored("[Logout]",'grey')+":logout OK"	
            if showMessage:
                res = QMessageBox.information(self, "Logout successful.", "You are now logged out.", QMessageBox.Ok)

            self.status = None
            self.setUserLoggedIn(None)
            self.ui.listWidget.clear()
            self.stopPsaEventThread()
            if self.useMobility:
                self.stopMobilityScript()
        else:
            if showMessage:
                print colored("[Logout]",'red')+":logout not OK"
                res = QMessageBox.critical(self, "An error occurred.", "Log out not successful.", QMessageBox.Ok)
        
    def login(self, user, pw):
        self.requestTask.user = user
        self.requestTask.pw = pw
        self.requestTask.start()
        return
        
    @QtCore.pyqtSlot()
    def authenticate(self):
        print "authenticate"
 

class AuthenticateDialog(QDialog, Ui_AuthenticateDialog):
    def __init__(self, description=None, parent=None):
        QDialog.__init__(self, parent)
        self.controller = parent
        self.ui = uic.loadUi("authenticate.ui")
        self.ui.hide()
    
        self.descr = description
        self.connect(self.ui.okButton, SIGNAL('clicked()'), self.buttonClicked)
        
    def show(self):
        self.ui.exec_()
        
    def buttonClicked(self):
        user = str(self.ui.lineEdit_user.text())
        pw = str(self.ui.lineEdit_passwd.text())
        print colored("[Login]",'grey')+": User login:" + user
        linestr = user + ":" + pw
        
        self.controller.login(user, pw)

    def accept(self):
        print "accept"
        
    def on_acceptBtnClicked(self):
        print "on_acceptBtnClicked"

    def on_rejectBtnClicked(self):
        print "on_rejectBtnClicked"

        
class AttestationRequestThread(QtCore.QThread):
    requestTaskFinished = QtCore.pyqtSignal()
    
    def __init__ (self, config):
        QThread.__init__(self)
        self.config = config
        # timeout (in seconds) to wait for verifier request
        self.TIMEOUT = 5.000
        self.trusted = False
        self.validate_time = None
        self.test = 0
        self.currentAP = ""
        
    def run(self):
        while True:
            self.trusted = False
            self.issuePollAttestation()
            sleep(self.config.getint('IPSEC','ATTESTATION_TIME'))
        
    def stop(self):
        try:
            self.terminate()
        except:
            self.quit()
            self.wait()
    
    def sendSignal(self):
        self.requestTaskFinished.emit()
        
    def issuePollAttestation(self):
        validate_time = "-"
        pollhost_url = self.config.get('VERIFIER','VERIFIER_URL')
        ned_name_verifier = self.config.get('NED','NED_ID')
        digest = ""
        try:
            ned_name_verifier = self.config.get('VERIFIER', self.currentAP)
        except Exception as e:
            print ">> Using default ned name for verifier:" + ned_name_verifier 
        try:
            digest = self.config.get('VERIFIER_DIGESTS', ned_name_verifier)
        except Exception as e:
            print e

        print colored("[AttestationRequestThread]",'blue')+": NED: " + ned_name_verifier + " DIGEST: " + digest
        # DEFINE THE JSON DATA 
        # NOTE: HARDCODED INTEGRITY HERE
        postData = {"hosts":[ned_name_verifier],"analysisType":"load-time+check-cert,"+self.config.get('VERIFIER','INTEGRITYLEVEL4')+",cert_digest="+digest}
        postData = json.dumps(postData)
        result = "untrusted"
        r = None
        try:
            r = requests.post(pollhost_url, data=postData, headers={'Content-Type':'application/json'}, verify=False, timeout=self.TIMEOUT)
        except Exception, e:
            pass
            print e

        if r != None:
            temp = None
            try:
                temp = r.json()
                result = temp['results'][0]['trust_lvl']
            except Exception, e:
                result = None
                print colored("[AttestationRequestThread]",'red')+": ERROR: parsing attestation result:" + str(temp)
                print e
                
            try:
                validate_time = temp['results'][0]['validate_time']
                self.test += 1
            except Exception, e:
                validate_time = None
        else:
            print colored("[AttestationRequestThread]",'red')+": ERROR: no valid response from verifier!"
            result = None
        
        # Now there's only handling for trusted or anything else
        if result == "trusted":
            print colored("[AttestationRequestThread]",'blue')+": NED is still trusted"
            self.trusted = True
        elif result == "untrusted":
            print colored("[AttestationRequestThread]",'red')+": NED IS UNTRUSTED!"
            self.trusted = False
        elif result == "vtime-err":
            self.trusted = False
        elif result == "cert-err":
            self.trusted = False
        else:
            print "-no valid response from verifier"
            self.trusted = None
        
        # Update time if available
        self.validate_time = validate_time
        self.requestTaskFinished.emit()


        
class LoginAvailableTaskThread(QtCore.QThread):
    requestTaskFinished = QtCore.pyqtSignal()
    
    def __init__ (self, arg):
        QThread.__init__(self)
        self.ned_url = arg
        self.status = False
        self.timeout = 0.5
        self.count = 0
        
    def run(self):
        self.tryLoginPage()
        
    def sendSignal(self):
        self.requestTaskFinished.emit()
        
    def tryLoginPage(self):
        url = self.ned_url + "login"
        
        self.r = None
        try:
            self.r = requests.get(url, timeout=self.timeout)
            self.status = True
        except Exception, e:
            self.status = False
            
        self.sendSignal()
                
class RequestTaskThread(QtCore.QThread):
    requestTaskFinished = QtCore.pyqtSignal()
    
    def __init__ (self, arg):
        QThread.__init__(self)
        self.ned_url = arg
        self.user = None
        self.pw = None
        
    def run(self):
        print colored("[RequestTaskThread]",'brown')+": RequestTaskThread Running."
        self.status = False
        self.timeout = 2.000
        self.login(self.user, self.pw)
        print colored("[RequestTaskThread]",'brown')+": RequestTaskThread Run Ended."
        
    def sendSignal(self):
        self.requestTaskFinished.emit()
        
    def login(self, user, pw):
        a = {}
        a["user"] = user
        a["password"] = pw
        url = self.ned_url + "login"
        
        self.r = None
        try:
            self.r = requests.post(url, data=json.dumps(a), headers={'Content-Type':'application/json'}, timeout=self.timeout)
        except Exception, e:
            print e
        
        # Timeout or other exception
        if self.r == None:
            self.sendSignal()
            return
        
        status = False
        if self.r.status_code == 200:
            print colored("[Login]",'grey')+": login OK: " + user
            status = True
        else:
            print colored("[Login]",'red')+": login not OK: " + user
        
        self.status = status
        self.sendSignal()

class PSCCommunicationThread(QtCore.QThread):

    def __init__ (self):
        QThread.__init__(self)

    def run(self):
        self.issuePollPSC()
        
    def sendResults(self, result):
        self.emit(SIGNAL('event_psa_list(QString)'), result)

    def issuePollPSC(self):
        self.connectionException = False
        not_communicated = True
        while not_communicated:
            try:
                psc_url = "http://10.2.2.251:8080/psc/get-psa-list"
                response = requests.get(psc_url, timeout=10.000)

                r = json.loads(response.text)
                if self.connectionException:
                    self.connectionException = False
                if len(r) == 0:
                    continue

                not_communicated = False
                self.sendResults(json.dumps(r))
            except Exception, e:
                print colored("[PSCCommunicationThread]",'red')+": PSC not reachable yet."
                if not self.connectionException:
                    self.connectionException = True
                sleep(2)
        print colored("[PSCCommunicationThread]",'brown')+": PSC COMMUNICATION THREAD EXITED   "


class PsaEventThread(QThread):
    def __init__(self, psa):
        QThread.__init__(self)
        self.psa_id = psa
        self.index = 0

    def stopThis(self):
        print "stopping."
        self.terminate()

    def __del__(self):
        self.wait()

    def getPsaEvents(self, psa_id):
        psc_url = "http://10.2.2.251:8080/psa/get-event-psa/" + psa_id
        response = None
        try:
            response = requests.get(psc_url, timeout=3.000)
        except Exception, e:
            pass
        return response

    def run(self):
        while True:
            #print "# Checking PSA events\n"
            r = self.getPsaEvents(self.psa_id)
            if r != None and r.status_code == 200:
                events = r.json()
                info = ""
                count = 0
                while len(events) > self.index:
                    # policy_id contains high-level policy info
                    #extra_info = events[self.index]["policy_id"]
                    title = events[self.index]["event_title"]
                    event = events[self.index]["event_body"]
                    count += 1
                    info += "#"+str(count)+": " + title +"\n" + event + "\n\n"
                    self.index += 1

                if info != "":
                    self.emit(SIGNAL('add_event(QString, QString)'), self.psa_id, info)
            else:
                print "PSA events response: " + str(r)

            # Depending on the count, query less frequently
            if self.index == 0:
                self.sleep(2)
            else:
                self.sleep(5)


if __name__ == "__main__":  
    app = QApplication(sys.argv) 
    ghui = GHUI()  
    sys.exit(app.exec_())
