#!/bin/sh
thisdir=`dirname "$0"`
thisdir=`cd "$thisdir" && pwd`

export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/redhawk/core/lib64
export PATH=$PATH:/usr/local/redhawk/core/bin
export SDRROOT="$thisdir"/sdr

DIGITIZER_NODE=/nodes/RTL2832_Node/DeviceManager.dcd.xml

usage() {
    cat <<EOFEOF
Usage: $0 [-sh]
 
   -h Show help
   -s Run with the RTL simulator
EOFEOF
}

err() {
    echo "$@" 1>&2
    exit 1
}

while getopts "hs" opt ; do
    echo "This is opt $opt"
    case "$opt" in 
        s) DIGITIZER_NODE=/nodes/sim_RX_DIGITIZER_Node/DeviceManager.dcd.xml ;;
        h) usage; exit 0 ;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done

pids=

# kill all remaining subprocesses at exit
trap 'kill -1 $pids' 0

mkdir -p logs || err

#NBARGS=--force-rebind --nopersist
NBARGS=

# Domain Manager
nodeBooter $NBARGS -D /domain/DomainManager.dmd.xml > logs/domain.log 2>&1 || err &
pids=$!

# GPP
nodeBooter $NBARGS -d /nodes/DevMgr_rhdemo1/DeviceManager.dcd.xml > logs/gpp.log 2>&1 || err &
pids="$pids $!"

# Digitizer
nodeBooter $NBARGS -d "$DIGITIZER_NODE" > logs/digitizer.log  2>&1 || err &
pids="$pids $!"

#FIXME: sleeps are horrible. Better to wait for device manager initializatio to complete
# before launching
#sleep 2
#scaclt install REDHAWK_DEV /waveforms/Rtl_FM_Waveform/Rtl_FM_Waveform.sad.xml
#scaclt create REDHAWK_DEV DCE:1ed946d9-3e77-4acc-8c2c-912641da6545 wform_21


# block until all subprocesses are killed. 
wait $pids
