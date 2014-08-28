#!/bin/sh
mydir=`dirname $0`
mydir=`cd "$mydir" && pwd`
TMPDIR="$mydir/tmp"

err() {
   echo "ERROR: $@"  1>&2
   exit 1
}

export SYSSDRROOT=/var/redhawk/sdr
SDRROOT="${mydir}/sdr"

if [ ! -e "${SYSSDRROOT}/$1" ] ; then
    err "$SYSSDRROOT/$1 does not exists"
fi

destdir=`dirname "$SDRROOT/$1"` || err
/bin/mkdir -p "$destdir" || err "Unable to create directory $destdir"
/bin/cp -L -r "${SYSSDRROOT}/$1" "$destdir" || err "Unable to copy $SYSSDRROOT/$1"
