#!/bin/bash

err() {
   echo "ERROR: $@"
   exit 1
}

mydir=`dirname "$0"` || err
mydir=`cd "$mydir" && pwd` || err
srcdir=`cd "$mydir/../server" && pwd` || err


# PROPERTIES

RHDOMAIN=REDHAWK_TEST
FM_SIMULATOR_ID='DCE:3d441470-8e96-4583-bef6-277446048814'

# FUNCTIONS
verify_domain() {
   scaclt list "$RHDOMAIN" | grep -q "$FM_SIMULATOR_ID" || err "REDHAWK Domain with the FM Simulator is not running. Use $0 -s to bootstrap the test domain."
}

usage() {
    cat <<EOFEOF
Usage: $0 [-hs]

    -h             Show help
    -s             Bootstrap the test environment
EOFEOF
}

bootstrap() {
   "$mydir"/startdomain.sh -r "$mydir/sdr" -d "$RHDOMAIN"
}

runtest() {
   verify_domain 
   (cd "$srcdir" &&  "$mydir"/../.virtualenv/bin/python /usr/bin/nosetests ./test.py)
}

PROGRAM=runtest
while getopts "hs" opt ; do
    case "$opt" in
        s) PROGRAM=bootstrap ;;
        h) usage; exit 0 ;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done
shift $((OPTIND-1))

$PROGRAM
