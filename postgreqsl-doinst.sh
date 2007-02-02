#!/bin/sh

###
# Place the postgresql init script.
###
config() {
  NEW="$1"
  OLD="`dirname $NEW`/`basename $NEW .new`"
  # If there's no config file by that name, mv it over:
  if [ ! -r $OLD ]; then
    mv $NEW $OLD
  elif [ "`cat $OLD | md5sum`" = "`cat $NEW | md5sum`" ]; then # toss the redundant copy
    rm $NEW
  fi
  # Otherwise, we leave the .new copy for the admin to consider...
}

config etc/rc.d/rc.postgresql.new

###
# Create postrgresql' user:group if they don't exist.
###
user_exists=`grep ^postgres etc/passwd`
if [[ "${user_exists}" == "" ]]; then
	useradd postgres
fi


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

