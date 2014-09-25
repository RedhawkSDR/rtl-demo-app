#!/bin/sh
thisdir=`dirname "$0"`
thisdir=`cd "$thisdir" && pwd`

export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/redhawk/core/lib64
export PATH=$PATH:/usr/local/redhawk/core/bin
export SDRROOT="$thisdir"/sdr
export RHDOMAIN=REDHAWK_DEV

DIGITIZER_NODE=/nodes/RTL2832_Node/DeviceManager.dcd.xml
FEIDEVICE=RTL2832U
startmsg='with RTL frontend node'
QUOTES=\'\"
DQUOTE=\"

usage() {
    cat <<EOFEOF
Usage: $0 [-sh]
 
   -d DOMAIN
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
      [ -e /proc/$pid ] && /usr/bin/kill -1 "$pid" 
   done
}

while getopts "hsd:" opt ; do
    case "$opt" in 
        s) DIGITIZER_NODE=/nodes/sim_RX_DIGITIZER_Node/DeviceManager.dcd.xml
           FEIDEVICE=sim_RX_DIGITIZER
           startmsg='with RTL simulator node' ;;
        d) RHDOMAIN="$OPTARG" ;;
        h) usage; exit 0 ;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done

pids=

# kill all remaining subprocesses at exit
trap 'killif $pids' 0 1 2 15

mkdir -p logs || err

sed -i "/refid=.DomainName/ s/value=[$QUOTES][^$QUOTES]*[$QUOTES]/value=${DQUOTE}${RHDOMAIN}${DQUOTE}/
        /refid=.FEIDeviceName/ s/value=[$QUOTES][^$QUOTES]*[$QUOTES]/value=${DQUOTE}${FEIDEVICE}${DQUOTE}/" \
              "$SDRROOT/dom/waveforms/Rtl_FM_Waveform/Rtl_FM_Waveform.sad.xml" || err

#NBARGS=--force-rebind --nopersist
NBARGS=--nopersist

# Domain Manager
nodeBooter $NBARGS -D /domain/DomainManager.dmd.xml --domainname $RHDOMAIN > logs/domain.log 2>&1 || err &
pids=$!

# GPP
nodeBooter $NBARGS -d /nodes/DevMgr_rhdemo1/DeviceManager.dcd.xml --domainname $RHDOMAIN > logs/gpp.log 2>&1 || err &
pids="$pids $!"

# Digitizer
nodeBooter $NBARGS -d "$DIGITIZER_NODE" --domainname $RHDOMAIN > logs/digitizer.log  2>&1 || err &
pids="$pids $!"

echo "Started $RHDOMAIN domain $startmsg. Use Ctrl-C to halt"

#FIXME: sleeps are horrible. Better to wait for device manager initializatio to complete
# before launching
#sleep 2
#scaclt install REDHAWK_DEV /waveforms/Rtl_FM_Waveform/Rtl_FM_Waveform.sad.xml
#scaclt create REDHAWK_DEV DCE:1ed946d9-3e77-4acc-8c2c-912641da6545 wform_21


# block until all subprocesses are killed. 
wait $pids
