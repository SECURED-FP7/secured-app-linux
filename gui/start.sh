#!/bin/bash


#/usr/libexec/strongswan/stroke up $1
echo "connecting to IPSEC connection: "$1
/usr/sbin/ipsec up $1
