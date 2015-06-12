# Adapted for vxi11_python use by khaho from original Makefile on vxi11 software
# Swig compiling needs a bit different approach, but changes are minimal.

VERSION=1.08

#CFLAGS = -Wall -g
CFLAGS =  -I/usr/include/python2.7 -fPIC
INSTALL = install
prefix = /usr/local
CC = c++

.PHONY : install clean dist distclean

all: _vxi11_python.so


_vxi11_python.so: vxi11_python_wrap.o vxi11_python.o vxi11_1.10/vxi11_user.o vxi11_1.10/vxi11_clnt.o vxi11_1.10/vxi11_xdr.o
	c++ -shared -fPIC -o $@ $^

vxi11_python_wrap.o: vxi11_python_wrap.cxx
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_python_wrap.cxx : vxi11_python.i
	swig -python -c++ vxi11_python.i
	
vxi11_python.o: vxi11_python.cc vxi11_1.10/vxi11_user.cc vxi11_1.10/vxi11.h
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_python.pyc: vxi11_python_wrap.cxx
	echo "import vxi11_python; quit()" | python
		
vxi11_1.10/vxi11_user.o: vxi11_1.10/vxi11_user.cc
	$(CC) $(CFLAGS) -c $< -o $@

vxi11_1.10/vxi11.h vxi11_1.10/vxi11_clnt.c vxi11_1.10/vxi11_xdr.c vxi11_1.10/vxi11_user.cc : vxi11_1.10/vxi11.x
	-(cd vxi11_1.10; rpcgen -M vxi11.x)

vxi11_1.10/vxi11.x::
	-(tar xzf vxi11_1.10.tar.gz --exclude vxi11_1.10/.bzr* > /dev/null)
		
TAGS: $(wildcard *.c) $(wildcard *.h) $(wildcard *.cc)
	etags $^	

	
install:: _vxi11_python.so vxi11_python.py vxi11_python.pyc scopeio.py
	sudo install -D _vxi11_python.so $(PREFIX)/bin/
	sudo install -D vxi11_python.py $(PREFIX)/bin/
	sudo install -D vxi11_python.pyc $(PREFIX)/bin/
	sudo install -D scopeio.py $(PREFIX)/bin/
	
clean:
	rm -rf vxi11_1.10 *.o _vxi11_python.so vxi11_python.py vxi11_python.pyc vxi11_python_wrap.cxx

