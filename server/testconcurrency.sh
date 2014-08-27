#!/bin/sh

url=http://localhost:8888/survey
data='{ "frequency": 123131123, "processing": "fm" }'
n=500
i=0
date1=`date +"%s"`
while [ $i -lt $n ] ; do
    curl -w " $i\n" --data "${data}" $url &
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
