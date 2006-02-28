#!/bin/sh

###
# Place the hal init script.
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
config etc/rc.d/rc.hald.new

###
# Create hal's user:group if they don't exist.
###
group_exists=`grep ^haldaemon etc/group`
if [[ "${group_exists}" == "" ]]; then
	groupadd haldaemon
fi
user_exists=`grep ^haldaemon etc/passwd`
if [[ "${user_exists}" == "" ]]; then
	useradd haldaemon -g haldaemon
fi

###
# Use rc.local to start hal at boot.
###
if [ ! -e etc/rc.d/rc.local ]; then
	echo "#!/bin/sh" > etc/rc.d/rc.local
	chmod 755 etc/rc.d/rc.local
fi
run=`grep "sh /etc/rc.d/rc.hald" etc/rc.d/rc.local`
if [[ "${run}" == "" ]]; then
	echo "" >> etc/rc.d/rc.local
	echo "if [ -x /etc/rc.d/rc.hald ]; then" >> etc/rc.d/rc.local
	echo "	sh /etc/rc.d/rc.hald start" >> etc/rc.d/rc.local
	echo "fi" >> etc/rc.d/rc.local
fi

# make sure sysfs exists in /etc/fstab
sysfs=`grep "sysfs" etc/fstab`
if [[ "${sysfs}" == "" ]]; then
	echo "none		/sys		sysfs		defaults	0   0" >> etc/fstab
fi
if [ ! -d sys ]; then
	mkdir -p sys
fi
