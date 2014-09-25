#!/bin/sh

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

pyvenv="${SCRIPTPATH}/pyvenv"
if [ ! -f ${pyvenv} ]; then
  pyvenv=/var/redhawk/web/bin/pyvenv
fi

source /etc/profile.d/redhawk.sh

exec ${pyvenv} python ${SCRIPTPATH}/server/server.py $@
