# The SECURED App

The SECURED App pretends to be the app the user uses to connect, login and manage his/her policies. 
When the app is started it automatically starts checking if the NED is trusted. If it is, then it 
enables a secured tunnel to it and allow the user to login. Once the user is logged in, his/her 
policies will be enforced. If the APP is configured to enable mobility, it will start sending 
reports to the NED, including the signal strenght of all the access points around (only the ones configured).

## Requirements

- Configured Trusted IPsec tunnels to all the NEDs around
- Linux system


## Dependencies
Dependencies for CentOS:
```bash
root@userterminal: # yum install gcc rmp-build yum-utils automake autoconf libtool pkg-config gettext perl python flex bison gperf libjson-c libjson-c-devel libsoup libsoup-devel
```

Dependencies for Ubuntu:
```bash
root@userterminal: # apt-get install  gcc  automake autoconf libtool pkg-config gettext perl python flex bison gperf libjson-c-dev libjson0  libjson0-dev libsoup2.4-dev libsoup2.4-1
```


## Configuration steps

Step 5 is used to configure the remote attestation feature, the rest are used to install and configure strongswan ipsec connection.

1. map hardcoded IP addresses with the verifer and NED in order to understand the roles in the system, further to simplify the configuration of attestation plugin;

2. download the source code of strongswan and install it;

    ```bash
    user@userterminal: $ cd strongswan-5.3.2
    user@userterminal: $ autoreconf -i
    user@userterminal: $ ./configure --with-ipsecdir=/usr/libexec/strongswan        --bindir=/usr/libexec/strongswan --sysconfdir=/etc/strongswan \
	 --enable-oat-attest --enable-soup --enable-eap-md5 \
       --enable-kernel-libipsec

    user@userterminal: $ make
    root@userterminal: # make install
    ```
3. copy ipsec configuration files from the ipsec directory to /etc/strongswan directory

 	ipsec.secrets is ready for use, the ip address in ipsec.conf needs to be modified based on the specific setting.

 	you can follow the descriptions in [strongswan ipsec.conf](https://wiki.strongswan.org/projects/strongswan/wiki/ConnSection) to customise your ipsec configurations.


4. copy the CA certificate from the NED it is connecting to, see [NED's README step 7](https://gitlab.secured-fp7.eu/secured/ned/blob/strongswan/strongswan/README.md);

5. replace the oat_attest.conf file from ipsec directory to /etc/strongswan/strongswan.d/charon/ directory;

	if no attestation feature is required, just change the 'load' option in oat_attest.conf to 'no'.

6. run strongswan by running starter script in /usr/libexec/strongswan

	```bash
	root@userterminal: # ./starter --daemon charon --nofork
	```

7. Modify the configuration file adapting it to your situation

## Configuration file

The configuration file for the app is located in app/gui/gui.conf. There are some comments inside which allow you to understand each parameter but the main idea is:
    - Enable/disable Mobility
    - Configure the verifier URL 
    - Define the parameters to send to the verifier depending on the current access point (ned name and digest)
    - If mobility is enabled, define the IPSEC connection name depending on the current AP

There is another configuration file: app/gui/ssids_list which only works when mobility is enabled. It must contain the list of ssids that the Mobility reporting will consider. This is, the ssids associated with a different ned.

## Performance Description

1. Raise the secured tunnel to the NED

    Mobility disabled: the IPSEC connection name will be defined in the conig by the IPSEC_NED_CONNECTION_NAME.

    Mobility enabled: Depending on the current access point and the configuration the app will raise the IPSEC connection 

2. Login to the NED

    The app will show a login form in a popup once the NED is accessible.

3. Start attestation thread

    Start checking continuously if the NED the client is connected to is trusted or not.

4. Start Mobility Client (Only if mobility is enabled)

    Start sending reports to the NED. The reports include the signal strenght of the wifi access points the client can see, but only the ones in the ssids_list file.


