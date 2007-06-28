
###
# Use rc.local to start avahi at boot.
###
if [ ! -e etc/rc.d/rc.local ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local
	chmod 755 etc/rc.d/rc.local
fi
run=`grep "sh /etc/rc.d/rc.avahidaemon" etc/rc.d/rc.local`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local
	echo "# start avahi daemon" >> etc/rc.d/rc.local
	echo "if [ -x /etc/rc.d/rc.avahidaemon ]; then" >> etc/rc.d/rc.local
	echo "	sh /etc/rc.d/rc.avahidaemon start" >> etc/rc.d/rc.local
	echo "fi" >> etc/rc.d/rc.local
fi
