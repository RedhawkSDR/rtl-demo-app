#!/bin/sh

url=http://localhost:8888/survey
n=50
i=0
date1=`date +"%s"`
while [ $i -lt $n ] ; do
    curl -w " $i\n" $url &
    i=$((i+1))
done
date2=`date +"%s"`

# wait for subprocesses to complete
diff=$((date2-date1))
echo "Fork took $diff seconds"
wait
