# Requires python 2.7x and python-qt4.

Installing on Ubuntu 14.04


# Install libraries

sudo apt-get install python-qt4
sudo apt-get install gksu 

Note: gksu is used for graphical sudo password asking. Modify ipsec script to use sudo instead of gksu if you don't want graphical password query.


# Modify for your setup

0. Change permission to files `start_gui` `ipsec` and `SECURED.desktop` in order to make them executable (`chmod +x filename`)


1. Modify `SECURED.desktop` 

This file allows to show an icon that can be double-clicked from your desktop in order to launch the application.
However, you have to modify the following lines in order to allow the icon to point to the actual folder where the app is located:

```
Path=/home/test/git/app/gui
Icon=/home/test/git/app/gui/SECURED_logo.png
Exec=/home/test/git/app/gui/start_gui
```

Furthermore, this file can be copied on your Linux Desktop in order to allow user to locate immediately the SecuredApp.

Note 1: You can also enable script starting, in which you separately start strongswan as sudo and python as normal user. See commented lines in SECURED.desktop and start_gui.

Note 2: If you don't want terminal for python debug prints, disable terminal in SECURED.DESKTOP. 

2. Modify `ipsec` script

ipsec script actually starts the strongswan. This is called from client_sec.py (IPSEC_START_CMDS)

3. Modify `client_sec.py` 

(See the file for CONFIGURATION which are on capital letters.)
- There's also numbered lines, e.g., 1 ------, which should be checked for the configuration.

```
        self.ATTESTATION_TIME = 3
        self.IPSEC_NED_CONNECTION_NAME = "test-ned"
        self.CERT_FILE = "/home/test/app/gui/certfile.cer"
        self.CERT_DIGEST = "8b71648e9c52a24cfe259305c611483ea56ca4dc"

        self.NED_ID = "test-ned"
        self.VERIFIER_URL = "http://verifier:8899"
        # INTEGRITY_LVL_NUMBER is used in verifier web page request.
        self.INTEGRITY_LVL_NUMBER = 4
        self.INTEGRITYLEVEL4 = "l_req=l4_ima_all_ok|>="
        self.USED_INTEGRITY = self.INTEGRITYLEVEL4
	self.USE_WEB = False
```

self.USE_WEB is the default value whether to use Verifier Web page to show results or app's GUI.
This can be changed from File-> menu.


# Running 

- Double click the' SECURED App' shortcut.
- python client_main.py 

1. It will ask for sudo password, since strongswan needs to be started as sudo/root. Disable if want. After that, the GUI is started and after login page is available, it will ask for user's password. Note: ipsec script kills previous strongswan. You can disbale it at ipsec script.


2. Strongswan terminal is opened in the background, you have to close it separately for now after closing the secured app. 


3. Menu 

File-> menu can be used to logout/login.

File-> Menu can be used to switch views (web page attestation / app authentication GUI)
