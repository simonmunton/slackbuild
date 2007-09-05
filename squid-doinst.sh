
# Keep same perms on rc.squid.new:
if [ -e etc/rc.d/rc.squid ]; then
  cp -a etc/rc.d/rc.squid etc/rc.d/rc.squid.new.incoming
  cat etc/rc.d/rc.squid.new > etc/rc.d/rc.squid.new.incoming
  mv etc/rc.d/rc.squid.new.incoming etc/rc.d/rc.squid.new
fi

###
# Use rc.local to start squid at boot.
###
if [ ! -e etc/rc.d/rc.local ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local
	chmod 755 etc/rc.d/rc.local
fi
run=`grep "sh /etc/rc.d/rc.squid" etc/rc.d/rc.local`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local
	echo "# start squid" >> etc/rc.d/rc.local
	echo "if [ -x /etc/rc.d/rc.squid ]; then" >> etc/rc.d/rc.local
	echo "	sh /etc/rc.d/rc.squid start" >> etc/rc.d/rc.local
	echo "fi" >> etc/rc.d/rc.local
fi

###
# Use rc.local_shutdown to stop squid at shutdown.
###
if [ ! -e etc/rc.d/rc.local_shutdown ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local_shutdown
	chmod 755 etc/rc.d/rc.local_shutdown
fi
run=`grep "sh /etc/rc.d/rc.squid" etc/rc.d/rc.local_shutdown`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local_shutdown
	echo "# stop squid" >> etc/rc.d/rc.local_shutdown
	echo "if [ -x /etc/rc.d/rc.squid ]; then" >> etc/rc.d/rc.local_shutdown
	echo "	sh /etc/rc.d/rc.squid stop" >> etc/rc.d/rc.local_shutdown
	echo "fi" >> etc/rc.d/rc.local_shutdown
fi
