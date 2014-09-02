#!/bin/sh

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

curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
curl -w " $i\n" -X DELETE http://localhost:8888/survey &
wait