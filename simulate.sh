#!/bin/sh -e
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
#
# This script will create a local SDR root, start a REDHAWK_SIM domain
# with the simulator device, and run the rtl_demo
# app against this domain.

thisdir=`dirname "$0"`
thisdir=`cd "$thisdir" && /bin/pwd`

# kill all processes when killed or we exit
trap "/bin/kill -1 -$$" 0 1 2 15

bin/mksdr.sh
bin/startdomain.sh -d 'REDHAWK_SIM' -r "$thisdir"/bin/sdr -s &
./start.sh --domain='REDHAWK_SIM' --simulate "$@" &
wait
