#!/bin/sh

###
# Place the dbus init script.
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
config etc/rc.d/rc.messagebus.new

###
# Create dbus' user:group if they don't exist.
###
group_exists=`grep ^messagebus etc/group`
if [[ "${group_exists}" == "" ]]; then
	groupadd messagebus
fi
user_exists=`grep ^messagebus etc/passwd`
if [[ "${user_exists}" == "" ]]; then
	useradd messagebus -g messagebus
fi

###
# Use rc.local to start dbus at boot.
###
PIDFILE=/var/run/dbus/dbus.pid
if [ ! -e etc/rc.d/rc.local ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local
	chmod 755 etc/rc.d/rc.local
fi
run=`grep "sh /etc/rc.d/rc.messagebus" etc/rc.d/rc.local`
if [[ "${run}" == "" ]]; then	
	echo "" >> etc/rc.d/rc.local
	echo "case \`uname -r\` in" >> etc/rc.d/rc.local
	echo "2.6*)" >> etc/rc.d/rc.local
	echo "if [ -x /etc/rc.d/rc.messagebus ]; then" >> etc/rc.d/rc.local
	echo "	if [ -w $PIDFILE ]; then" >> etc/rc.d/rc.local
	echo "		rm $PIDFILE" >> etc/rc.d/rc.local
	echo "	fi" >> etc/rc.d/rc.local
	echo "	sh /etc/rc.d/rc.messagebus start" >> etc/rc.d/rc.local
	echo "fi" >> etc/rc.d/rc.local
	echo ";;" >> etc/rc.d/rc.local
	echo "esac" >> etc/rc.d/rc.local
fi
