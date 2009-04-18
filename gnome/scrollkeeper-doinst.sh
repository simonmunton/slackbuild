#
echo "`date +\"%b %d %X\"` Installing ScrollKeeper `scrollkeeper-config --version`..." >> /var/log/scrollkeeper.log
/usr/bin/scrollkeeper-rebuilddb -q -p /var/lib/scrollkeeper

if [ -x /usr/bin/scrollkeeper-update ]; then
  /usr/bin/scrollkeeper-update -p /var/lib/scrollkeeper 1> /dev/null 2> /dev/null
fi

