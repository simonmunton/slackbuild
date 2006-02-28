#!/bin/sh
CWD=`pwd`

echo "YODESTDIR=$DESTDIR"

VERSION=2.1.7
ARCH=${ARCH:-i486}

if [ "$ARCH" = "i386" ]; then
  SLKCFLAGS="-O2 -march=i386 -mcpu=i686"
elif [ "$ARCH" = "i486" ]; then
  SLKCFLAGS="-O2 -march=i486 -mcpu=i686"
elif [ "$ARCH" = "s390" ]; then
  SLKCFLAGS="-O2"
elif [ "$ARCH" = "x86_64" ]; then
  SLKCFLAGS="-O2"
fi

cat << EOF

***************************************************
* Building freetype-$VERSION
***************************************************

EOF

# Step one is to remove existing freetype2 cruft:
rm --verbose -rf $DESTDIR/usr/include/freetype2 \
       $DESTDIR/usr/X11R6/include/freetype2 \
       $DESTDIR/usr/X11R6/include/ft2build.h \
       $DESTDIR/usr/lib/libfreetype.* \
       $DESTDIR/usr/X11R6/lib/libfreetype.* \
       $DESTDIR/usr/X11R6/bin/freetype-config
# It seems prudent to move this into /usr rather than /usr/X11R6, as *many* source bits
# won't find ft2build.h in /usr/X11R6/include without some patching.
# Therefore, --prefix=/usr must be the ad-hoc standard.  Another
# rationale:  /usr is also the prefix for freetype1 (for as long as that sticks around),
# and putting them in different prefixes causes problems.  Also, we're bumping the -march
# from i386 to i486, as I can't imagine too many people are running the latest Slackware
# with X on a 386 in the year 2002.  If there are, maybe they can get away with running an
# earlier version of X.  :-) 
cd /tmp
rm -rf freetype-$VERSION
tar xjvf $CWD/freetype-$VERSION.tar.bz2
cd freetype-$VERSION
# This breaks far too many things.  Freetype2 developers will have to get their
# punishment on someone else's distribution.
zcat $CWD/freetype.illadvisederror.diff.gz | patch -p1
chown -R root.root .
CFLAGS="$SLKCFLAGS" make setup CFG="--prefix=/usr $ARCH-slackware-linux"
make
make install DESTDIR=$DESTDIR
ldconfig
# This shouldn't be needed (apps should pick up -I/usr/include/freetype2 from
# `freetype-config --cflags` while compiling), but it's so often reported as a bug that
# I'll give in to the point.  Now that Freetype1 is pretty much gone having this link
# shouldn't hurt anything.  Try not to rely on it, though.
mkdir -p $DESTDIR/usr/include
( cd $DESTDIR/usr/include
  rm -rf freetype
  ln -sf freetype2/freetype .
)
mkdir -p $DESTDIR/usr/X11R6/lib/X11/doc
cp -a docs $DESTDIR/usr/X11R6/lib/X11/doc/freetype-$VERSION
rm -rf $DESTDIR/usr/X11R6/lib/X11/doc/freetype-$VERSION/reference

