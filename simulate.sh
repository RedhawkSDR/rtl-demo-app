#!/bin/sh -e
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
