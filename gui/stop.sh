#!/bin/bash

#/usr/libexec/strongswan/stroke down $1
echo "Disconnecting from IPSEC connection: "$1
/usr/sbin/ipsec down $1
