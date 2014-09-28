#!/bin/sh
mydir=`dirname $0`
mydir=`cd "$mydir" && pwd`
TMPDIR="$mydir/tmp"
export SRCSDR=${SDRROOT:-/var/redhawk/sdr}
DESTSDR="${mydir}/sdr"

err() {
   echo "ERROR: $@"  1>&2
   exit 1
}

warn() {
   echo "WARN: $@" 1>&2
}

alias errwarn=err

usage() {
    cat <<EOFEOF
Usage: $0 [-wh] [-s SDRROOT]

    -h             Show help
    -s SDRROOT     Use the given SDRROOT.  Defaults to $SRCSDR
    -w             Warn (do not fail) if asset does not exists
EOFEOF
}

while getopts "hs:w" opt ; do
    case "$opt" in
        s) SRCSDR=$OPTARG ;;
        h) usage; exit 0 ;;
        w) alias errwarn=warn ;;
        *) err "BAD PARAMETER $opt" ;;
    esac
done
shift $((OPTIND-1))

if [ ! -e "${SRCSDR}/$1" ] ; then
    errwarn "$SRCSDR/$1 does not exist" && exit 0
fi

destdir=`dirname "$DESTSDR/$1"` || err
/bin/mkdir -p "$destdir" || err "Unable to create directory $destdir"
/bin/cp -L -r "${SRCSDR}/$1" "$destdir" || err "Unable to copy $SRCSDR/$1"
