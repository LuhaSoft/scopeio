
def cmdresp(clink, cmd, returntype='ASC'):
    try:
        rlen = vxi11.cmd(self.clink,cmd)
    except:
        if returntype == 'ASC':
            return ''
        else:
            return bytearray()
    bresp = bytearray()
    i = 0
    while rlen >= 8:
        try:
            bresp.extend(pack('q',vxi11.resp(self.clink,i)))
        except:
            break
        i += 1
        rlen -= 8
    if rlen > 0:
        bresp.extend(pack('q',vxi11.resp(self.clink,i))[0:rlen])                
    if type == 'ASC':
        return str(bresp)
    return bresp
