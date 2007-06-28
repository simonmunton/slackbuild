#!/bin/sh
ID="$1"
MODULE=`modprobe -c | grep -w "$ID" | uniq | cut -f3 -d' '`
if ! modprobe -c | grep -q "^blacklist.*$MODULE" ; then
	modprobe $ID
fi
