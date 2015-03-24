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
Usage: $0 [-hs] [--] [nosetests args]

    -h             Show help
    -s             Bootstrap the test environment
    -l             Show the domain logs
    --             Used to end $0 args, start nosttests args

Examples:
   $0 test:RTLAppTest.test_rds
   $0 -- -s test:RESTfulTest.test_streaming_ws
   To list the tests
   $0 -- -v --collect-only
EOFEOF
}

bootstrap() {
   "$mydir"/startdomain.sh -r "$mydir/sdr" -d "$RHDOMAIN"
}

runtest() {
   verify_domain 
   [ $# -lt 1 ] && set test 
   (cd "$srcdir" &&  set -x && "$mydir"/../.virtualenv/bin/python /usr/bin/nosetests1.1 "$@") 2>&1 | tee runtests.out
}

showlog() {
   less "$mydir"/sdr/dom/logs/* 
}

PROGRAM=runtest
while getopts "hls-" opt ; do
    case "$opt" in
        s) PROGRAM=bootstrap ;;
        l) PROGRAM=showlog ;;
        h) usage; exit 0 ;;
        -) break;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done
shift $((OPTIND-1))

$PROGRAM "$@"
