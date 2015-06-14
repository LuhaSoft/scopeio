vxi11/README.rst
=====
vxi11
=====

Simple conversion of vxi11 application to python module.

Quick start
-----------

1. Import module like this:

   import vxi11

2. Use the functions like this:

   st = vxi11.open('192.168.1.11','DeviceName')
   if st != 0:
	exit(0)

   len = vxi11.cmd('*IDN?');
   resp = ''
   i = 0
   while i < len;
	resp = resp + vxi11.resp(i);
	i += 1
   print(resp)

   st = vxi11.close('192.168.1.11');

