# Add QT library directory to /etc/ld.so.conf:
if fgrep /usr/lib/qt/lib etc/ld.so.conf 1> /dev/null 2> /dev/null ; then
  true
else
  echo "/usr/lib/qt/lib" >> etc/ld.so.conf
fi
if [ -x /sbin/ldconfig ]; then
  /sbin/ldconfig 2> /dev/null
fi
