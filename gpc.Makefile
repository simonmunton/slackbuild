# Unix/Linux makefile for GPC 2.31
#
# Riley Rainey  (riley.rainey@websimulations.com)

CFLAGS = -O -g

libgenpolyclip.a: gpc.o
	rm -f $@
	ar cr $@ $<
	ranlib $@

clean:
	rm -f libgenpolyclip.a *.o core *~

install: libgenpolyclip.a
	-mkdir -p $(DESTDIR)/usr/lib
	-mkdir -p $(DESTDIR)/usr/include
	install libgenpolyclip.a $(DESTDIR)/usr/lib/libgenpolyclip.a
	install gpc.h $(DESTDIR)/usr/include/gpc.h
