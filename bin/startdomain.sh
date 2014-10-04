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

RHDOMAIN=REDHAWK_DEV

DIGITIZER_NODE=/nodes/RTL2832_Node/DeviceManager.dcd.xml

GPP_NODE_NAME=RTL-Demo-GPP-Node
GPP_NODE=/nodes/${GPP_NODE_NAME}/DeviceManager.dcd.xml

FEIDEVICE=RTL2832U
startmsg='with RTL frontend node'
QUOTES=\'\"
DQUOTE=\"

usage() {
    cat <<EOFEOF
Usage: $0 [-sh]
 
   -d DOMAIN
   -r SDRROOT
   -h Show help
   -s Run with the RTL simulator
EOFEOF
}

err() {
    echo "$@" 1>&2
    exit 1
}

killif() {
   for pid in "$@" ; do
      [ -e /proc/$pid ] && /usr/bin/kill -TERM -$$ "$pid"
   done
}

anywait(){
   while true ; do
       for pid in "$@" ; do
           [[ ! -e /proc/$pid ]] && return
       done
       sleep .5
   done
}

while getopts "hsd:r:" opt ; do
    case "$opt" in 
        s) DIGITIZER_NODE=/nodes/sim_RX_DIGITIZER_Node/DeviceManager.dcd.xml
           FEIDEVICE=sim_RX_DIGITIZER
           startmsg='with RTL simulator node' ;;
        d) RHDOMAIN="$OPTARG" ;;
        r) export SDRROOT="$OPTARG"
           # make absolute
           export SDRROOT=`cd "$SDRROOT" && pwd` ;;
        h) usage; exit 0 ;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done

if [ -z "$OSSIEHOME" ]; then
  source /etc/profile.d/redhawk.sh
fi
if [ -z "$SDRROOT" ]; then
  source /etc/profile.d/redhawk-sdrroot.sh
fi

export LOGDIR="$SDRROOT"/dom/logs
mkdir -p ${LOGDIR}

pids=

# kill all remaining subprocesses at exit
trap 'killif $pids' 0 1 2 15

if [ ! -f "$SDRROOT/dev/$GPP_NODE" ]; then
  ${SDRROOT}/dev/devices/GPP/python/nodeconfig.py --domainname=${RHDOMAIN} --nodename=${GPP_NODE_NAME} --inplace
fi

# FIXME:  Should be waveform init properties from the rtl app
# modify the domain name and Front end device in waveform
sed -i "/refid=.DomainName/ s/value=[$QUOTES][^$QUOTES]*[$QUOTES]/value=${DQUOTE}${RHDOMAIN}${DQUOTE}/
        /refid=.FEIDeviceName/ s/value=[$QUOTES][^$QUOTES]*[$QUOTES]/value=${DQUOTE}${FEIDEVICE}${DQUOTE}/" \
              "$SDRROOT/dom/waveforms/RTL_FM_Waveform/RTL_FM_Waveform.sad.xml" || err

#NBARGS=--force-rebind --nopersist
NBARGS=--nopersist

# Domain Manager
nodeBooter $NBARGS -D /domain/DomainManager.dmd.xml --domainname $RHDOMAIN > "$LOGDIR"/domain.log 2>&1 || err &
pids=$!

# GPP
nodeBooter $NBARGS -d "${GPP_NODE}" --domainname $RHDOMAIN > "$LOGDIR"/gpp.log 2>&1 || err &
pids="$pids $!"

# Digitizer
nodeBooter $NBARGS -d "$DIGITIZER_NODE" --domainname $RHDOMAIN > "$LOGDIR"/digitizer.log  2>&1 || err &
pids="$pids $!"

echo "Started $RHDOMAIN domain $startmsg. Use Ctrl-C to halt"

# block until all subprocesses are killed. 
anywait $pids
