#!/bin/sh
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK rtl-demo-app.
#
# REDHAWK rtl-demo-app is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK rtl-demo-app is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
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