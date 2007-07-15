#!/bin/sh

if [ ! -d /var/lib/pgsql/data ]
then
  mkdir -p /var/lib/pgsql/data
  chown postgres /var/lib/pgsql/data

  (su - postgres -c "/usr/bin/initdb -D /var/lib/pgsql/data" )
fi

###
# Use rc.local to start postgresql at boot.
###
PIDFILE=/var/lib/pgsql/data/postmaster.pid

if [ ! -e etc/rc.d/rc.local ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local
	chmod 755 etc/rc.d/rc.local
fi
run=`grep "/etc/rc.d/rc.postgresql" etc/rc.d/rc.local`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local
	echo "if [ -x /etc/rc.d/rc.postgresql ]; then" >> etc/rc.d/rc.local
	echo "	if [ -w $PIDFILE ]; then" >> etc/rc.d/rc.local
	echo "		rm $PIDFILE" >> etc/rc.d/rc.local
	echo "	fi" >> etc/rc.d/rc.local
	echo "	/etc/rc.d/rc.postgresql start" >> etc/rc.d/rc.local
	echo "fi" >> etc/rc.d/rc.local
fi

if [ ! -e etc/rc.d/rc.local_shutdown ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local_shutdown
	chmod 755 etc/rc.d/rc.local_shutdown
fi
run=`grep "/etc/rc.d/rc.postgresql" etc/rc.d/rc.local_shutdown`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local_shutdown
	echo "if [ -x /etc/rc.d/rc.postgresql ]; then" >> etc/rc.d/rc.local_shutdown
	echo "	/etc/rc.d/rc.postgresql stop" >> etc/rc.d/rc.local_shutdown
	echo "fi" >> etc/rc.d/rc.local_shutdown
fi
