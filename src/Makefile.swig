# Adapted for vxi11_python use by khaho from original Makefile on vxi11 software
# Swig compiling needs a bit different approach, but changes are minimal.

VERSION=1.08

#CFLAGS = -Wall -g
CFLAGS =  -I/usr/include/python2.7 -fPIC
INSTALL = install
PREFIX = /usr/local
CC = c++

.PHONY : install clean dist distclean

all: pip/pip.vxi11cc/dist/vxi11cc-03.tar.gz pip/pip.vxi11conn/dist/vxi11conn-03.tar.gz

_vxi11cc.so: vxi11cc_wrap.o vxi11cc.o vxi11_1.10/vxi11_user.o vxi11_1.10/vxi11_clnt.o vxi11_1.10/vxi11_xdr.o
	c++ -shared -fPIC -o $@ $^

vxi11cc_wrap.o: vxi11cc_wrap.cxx
	$(CC) $(CFLAGS) -c $< -o $@

vxi11cc_wrap.cxx : vxi11cc.i
	swig -python -c++ vxi11cc.i
	
vxi11cc.o: vxi11cc.cc vxi11_1.10/vxi11_user.cc vxi11_1.10/vxi11.h
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_1.10/vxi11_user.o: vxi11_1.10/vxi11_user.cc
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_1.10/vxi11.h vxi11_1.10/vxi11_clnt.c vxi11_1.10/vxi11_xdr.c vxi11_1.10/vxi11_user.cc : vxi11_1.10/vxi11.x
	-(cd vxi11_1.10; rpcgen -M vxi11.x)

vxi11_1.10/vxi11.x::
	-(tar xzf vxi11_1.10.tar.gz --exclude vxi11_1.10/.bzr* > /dev/null)
		
TAGS: $(wildcard *.c) $(wildcard *.h) $(wildcard *.cc)
	etags $^	

pip/pip.vxi11cc/dist/vxi11cc-03.tar.gz: modules/vxi11cc/__init__.py _vxi11cc.so vxi11cc.py
	mkdir -p pip/pip.vxi11cc/vxi11cc
	cp modules/vxi11cc/* pip/pip.vxi11cc/vxi11cc/
	cp _vxi11cc.so vxi11cc.py pip/pip.vxi11cc/vxi11cc/
	(cd pip/pip.vxi11cc; python setup.py sdist)

pip/pip.vxi11conn/dist/vxi11conn-03.tar.gz: modules/vxi11conn/__init__.py modules/vxi11conn/vxi11conn.py
	mkdir -p pip/pip.vxi11conn/vxi11conn
	cp modules/vxi11conn/* pip/pip.vxi11conn/vxi11conn/
	(cd pip/pip.vxi11conn; python setup.py sdist)
	
install:: pip/pip.vxi11cc/dist/vxi11cc-03.tar.gz pip/pip.vxi11conn/dist/vxi11conn-03.tar.gz scopeio.py
	sudo install -D scopeio.py $(PREFIX)/bin/
	(cd pip/pip.vxi11cc; sudo pip install --upgrade dist/vxi11cc-0.3.tar.gz)
	(cd pip/pip.vxi11conn; sudo pip install --upgrade dist/vxi11conn-0.3.tar.gz)
	
clean:
	rm -rf vxi11_1.10/
	rm -rf pip/pip.vxi11cc/vxi11cc
	rm -rf pip/pip.vxi11conn/vxi11conn
	rm -f *.o *.so *.pyc vxi11cc.py vxi11cc_wrap.*
