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
