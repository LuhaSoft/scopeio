# Adapted for vxi11_python use by khaho from original Makefile on vxi11 software
# Swig compiling needs a bit different approach, but changes are minimal.

VERSION=1.08

#CFLAGS = -Wall -g
CFLAGS =  -I/usr/include/python2.7 -fPIC
INSTALL = install
PREFIX = /usr/local
CC = c++

.PHONY : install clean dist distclean

all: _vxi11.so


_vxi11.so: vxi11cc_python_wrap.o vxi11cc_python.o vxi11_1.10/vxi11_user.o vxi11_1.10/vxi11_clnt.o vxi11_1.10/vxi11_xdr.o
	c++ -shared -fPIC -o $@ $^

vxi11cc_python_wrap.o: vxi11cc_python_wrap.cxx
	$(CC) $(CFLAGS) -c $< -o $@

vxi11cc_python_wrap.cxx : vxi11cc_python.i
	swig -python -c++ vxi11cc_python.i
	
vxi11cc_python.o: vxi11cc_python.cc vxi11_1.10/vxi11_user.cc vxi11_1.10/vxi11.h
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_1.10/vxi11_user.o: vxi11_1.10/vxi11_user.cc
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_1.10/vxi11.h vxi11_1.10/vxi11_clnt.c vxi11_1.10/vxi11_xdr.c vxi11_1.10/vxi11_user.cc : vxi11_1.10/vxi11.x
	-(cd vxi11_1.10; rpcgen -M vxi11.x)

vxi11_1.10/vxi11.x::
	-(tar xzf vxi11_1.10.tar.gz --exclude vxi11_1.10/.bzr* > /dev/null)
		
TAGS: $(wildcard *.c) $(wildcard *.h) $(wildcard *.cc)
	etags $^	

	
install:: _vxi11cc.so vxi11cc.py vxi11pconn.py scopeio.py
	cp _vxi11cc.so vxi11cc.py pip/vxi11/
	cp vx11pconn.py pip/vxi11/__init__.py
	(cd pip; python setup.py sdist)
	(cd pip/dist; sudo pip install --upgrade vxi11-0.3.tar.gz)
	sudo install -D scopeio.py $(PREFIX)/bin/
	
clean:
	rm -rf vxi11_1.10/
	rm -f *.o *.so *.pyc vxi11cc.py vxi11cc_python_wrap.cxx pip/vxi11/*
