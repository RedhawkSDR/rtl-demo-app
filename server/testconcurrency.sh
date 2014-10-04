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

runtests() {
	local url data n i
	url="$1"
	data="$2"
	n=${3:-500}
	i=0
	date1=`date +"%s"`
	while [ $i -lt $n ] ; do
	    curl -w " $i\n" ${data:+--data} ${data:+"$data"} $url &
	    i=$((i+1))
	done
	date2=`date +"%s"`

	# wait for subprocesses to complete
	diff=$((date2-date1))
	echo "Fork took $diff seconds"
	wait
	date2=`date +"%s"`
	diff=$((date2-date1))
	echo "Tests took $diff seconds"
}

runtests "http://localhost:8888/survey" '{ "frequency": 123131123, "processing": "fm" }'
runtests "http://localhost:8888/survey"

curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
wait