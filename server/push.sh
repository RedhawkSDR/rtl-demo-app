#!/bin/sh

appdir=`dirname $0`
appdir=`cd "$appdir/.." && pwd`
DESTDIR=src/RTL_demo
#rsync -avz $appdir --exclude=.git  rhdemo1:$DESTDIR
rsync -avz $appdir rhdemo1:$DESTDIR
