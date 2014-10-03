#!/bin/sh
##################################################
# reset.sh
#
# Resets the RTL Demo including all of REDHAWK
#

# The clean way to stop
sudo service redhawk-web stop

# Brute force
ps -aef | grep REDHAWK_DEV | awk '{print $2}' | xargs kill -9

# Reset REDHAWK
sudo service omniEvents stop
sudo service omniNames stop

sudo rm /var/log/omniORB/*
sudo rm /var/lib/omniEvents/*

sudo service omniNames start
sudo service omniEvents start

# The clean way to start
sudo service redhawk-web start