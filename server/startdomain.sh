#!/bin/sh
export LD_LIRARY_PATH=/usr/local/lib
export PATH=$PATH:/usr/local/redhawk/core/bin

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

# kill all subprocesses at script exit
trap 'kill -1 $pids' 0

mkdir -p logs || err

# Domain Manager
nodeBooter --force-rebind --nopersist -D /domain/DomainManager.dmd.xml > logs/domain.log 2>&1 || err &
pids=$!

# GPP
nodeBooter --force-rebind --nopersist -d /nodes/DevMgr_rhdemo1/DeviceManager.dcd.xml > logs/gpp.log 2>&1 || err &
pids="$pids $!"

# Digitizer
nodeBooter --force-rebind --nopersist -d "$DIGITIZER_NODE" > logs/digitizer.log 2>&1 || err &
pids="$pids $!"

# block until all subprocesses are killed. 
wait $pids
