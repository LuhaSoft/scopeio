"""
vxi support for python
"""

#import sys
from _vxi11 import *

class pconn():
        def __init__(self):
                self.plink = None
        def connect(self,device_ip,buffer_size=1024*1024,device_name=''):
                self.plink = iconnect(device_ip,buffer_size,device_name)
                if self.plink == None:
                        return(False)
                return(True )       
        def command(self, cmd, timeout_ms, returntype='ASC'):
                if self.plink == None:
                        return(0)
                rlen = icommand(self.plink, cmd, timeout_ms)
                bresp = bytearray()
                ind = 0
                while rlen > 0:
                        resp = iresponse(self.plink,ind)
                        bresp.append(resp)
                        ind += 1
                        rlen -= 8
                if rlen < 0:
                        resp = resp[:rlen]
                if type == 'ASC':
                        return str(bresp)
                return bresp
        def disconnect(self)
                idisconnect(self.plink)
                self.plink = None
	def version():
		return 'v0.3';
                
