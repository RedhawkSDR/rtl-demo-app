#!/bin/sh

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

venv="${SCRIPTPATH}/.virtualenv"
pyvenv=${SCRIPTPATH}/pyvenv

case "$1" in

  install)
    if [ -d $venv ]; then
      echo "Removing old python virtualenv"
      rm -rf ${venv}
    fi

    virtualenv --system-site-packages ${venv}
    ${pyvenv} easy_install "tornado==4.0.1"
    ${pyvenv} easy_install "gevent==1.0.1"

    chown -R redhawk:redhawk ${venv}
  ;;

  uninstall)
    if [ -d $venv ]; then
      echo "Removing old python virtualenv"
      rm -rf ${venv}
    fi
  ;;

  *)
    echo "Usage: $0 {install|uninstall}"
  ;;
esac
