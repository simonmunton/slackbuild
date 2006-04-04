#!/bin/sh

###
# Place the avahi init script.
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
config etc/rc.d/rc.avahidaemon.new
config etc/rc.d/rc.avahidnsconfd.new
config etc/avahi/avahi-daemon.conf.new
config etc/avahi/avahi-dnsconfd.action.new
config etc/avahi/hosts.new
config etc/avahi/services/ssh.service.new
config etc/dbus-1/system.d/avahi-dbus.conf.new

###
# Create avahi' user:group if they don't exist.
###
group_exists=`grep ^avahi etc/group`
if [[ "${group_exists}" == "" ]]; then
	groupadd avahi
fi
user_exists=`grep ^avahi etc/passwd`
if [[ "${user_exists}" == "" ]]; then
	useradd avahi -g avahi
fi

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
