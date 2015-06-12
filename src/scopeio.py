#!/usr/bin/python

import os
import time
import errno
import subprocess
import shlex
import string
import sys
import pexpect

from numpy import *
import Gnuplot, Gnuplot.funcutils

import vxi11

class scopeIO():

        def __init__(self):
                self.prefix = 'scope'
                self.nomeas = False
                self.view   = ''
                self.screen = False
                self.screenmode = 'RUN'
                self.outformat = '.png'
                self.leftargv = []
                self.files = ''
                self.timescale = 1.0
                self.config = '~/.scopeio'
                self.addr = '0.0.0.0'
                self.nomodes = False
                self.mode = ''
                self.after = ''
                self.size='1000,640'
		self.sequence = 1
                self.device = 'Rigol_DS1054'
                
        def Usage(self):
                print('Usage: scopeio.py [--nomeas] [--nomodes] [--mode=state] [--after=state]')
                print('     [--help] [--prefix=namestart] [--view=program] [--format=<fmt>] ')
                print('     [--screen] [--noscreen] [--addr=a.b.c.d] [--config=filename]')
                print('     [--size=xsize,ysize] [channels] ... [channels]')
                print('')
                print('Default prefix is "scope".')
                print('Formats supported now: png (default) and svg.')
                print('Setting --nomodes means that scope is not stopped or run during capture.')
                print('Setting --mode=STOP or --mode=RUN is mode for measurement time and similarly')
                print('--after=STOP or --after=RUN is mode left on after measurement. Default is')
                print('not to change scope mode.')
                print('Default size is 1000,640 pixels, can be for example by --size=800,480, this')
                print('does not affect the screendump, which is always 800,480 from the scope')
                print('')
                print('Examples:')
                print('  scopeio.py --nomeas --view=mirage 1           -- ch1 shown in mirage with no measurements (faster)')
                print('  scopeio.py 12 34 13 23  --prefix=myfile       -- ch1/ch2 ch3/ch4 ch1/ch3 ch3/ch4 images done')
                print('  scopeio.py --view=gimp 1234 --format=svg      -- all 4 channels in svg and send to gimp')
                print('  scopeio.py --screen --mode=STOP               --- take only display screen dump, STOP the scope')
                print('  scopeio.py --screen 12 --nomodes              --- take screen dump and two channel graph, no STOP/RUN')
                print('  scopeio.py --addr=192.168.1.100 1 --noscreen  --- scope ip address set, no screen capture')
                print('  scopeio.py --config=~/.scopeio.myconfig       --- alternate config file, default is ~/.scopeio')
                print('')
                print('Default config file is  ~/.scopeio, all above settings can be there, one per line, same syntax,')
                print('lines starting with # are taken as comments.')
                
                exit(0)

        def ParseArgs(self, argv):
                for item in argv[1:]:
                        if item == '--nomeas':
                                self.nomeas = True
                        elif item == '--nomodes':
                                self.nomodes = True
                        elif item == '--help':
                                self.Usage()
                        elif item[0:7] == '--view=':
                                self.view = item[7:]
                        elif item[0:7] == '--addr=':
                                self.addr = item[7:]
                        elif item[0:7] == '--size=':
                                self.size = item[7:]
                        elif item[0:7] == '--mode=':
                                if item[7:] == 'RUN': 
                                        self.mode = 'RUN'
                                if item[7:] == 'STOP': 
                                        self.mode = 'STOP'
                        elif item[0:8] == '--after=':
                                if item[8:] == 'RUN': 
                                        self.after = 'RUN'
                                if item[8:] == 'STOP': 
                                        self.after = 'STOP'
                        elif item[0:8] == '--screen':
                                self.screen = True
                        elif item[0:10] == '--noscreen':
                                self.screen = False
                        elif item[0:9] == '--format=':
                                if item[9:12] == 'svg':
                                        self.outformat = '.svg'
                        elif item[0:9] == '--config=':
                                self.config = item[9:]
                        elif item[0:9] == '--prefix=':
                                self.prefix = item[9:]
                        else:
                                parsed=''
                                while item != '':
                                        if item[0] >= '1' and item[0] <= '4':
                                                parsed = parsed + item[0]
                                        item = item[1:]
                                if parsed != '':
                                        self.leftargv.append(parsed)


        def Cmd(self,cmd,waittime):
                cmd = cmd + '\n'
                sys.stdout.write('-')
                sys.stdout.flush()
                rlen = 0;
                try:
                        rlen = vxi11.cmd(cmd)
                except:
                        return 'Write timeout:' + cmd
                sys.stdout.write('.')
                sys.stdout.flush()
                resp = ''
                i = 0
                while rlen > 0:
                        resp = resp + vxi11.resp(i)
                        i += 1
                        rlen -= 1
                return resp

        def Waveform(self, channels):
                self.alldata = []
                print('')
                result = self.Cmd(':WAVEFORM:FORMAT ASCII', 20)
                result = self.Cmd(':WAVEFORM:POINT:MODE NORMAL', 20)
                result = self.Cmd(':TIMEBASE:MAIN:SCALE?', 20)
                self.timescale = float(result)
                self.min_value = 1e10
                self.max_value = -1e10
                while channels != '':
                        print('')
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
                        result = self.Cmd(':WAVEFORM:SOURCE ' + chnow,20)
                        data = self.Cmd(':WAVEFORM:DATA?',180)[11:]
                        data = data.split(',')
                        fdata = []
                        for item in data:
                                try:
                                        value = float(item)
                                except:
                                        break
                                if value < self.min_value:
                                        self.min_value = value
                                if value > self.max_value:
                                        self.max_value = value
                                fdata.append(value)
                        self.alldata.append(fdata)

        def Meas(self, channels):
                self.meas=[]
                while channels != '':
                        print('')
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
                        chmeas = chnow
                        if self.nomeas == False:
                                result = self.Cmd(':MEASURE:ITEM:VPP ' + chnow,20)
                                result = self.Cmd(':MEASURE:ITEM? VPP,' + chnow,20)
                                chmeas = chmeas + '  VPP:' + str(float(result))
                                result = self.Cmd(':MEASURE:ITEM:VMAX ' + chnow,20)
                                result = self.Cmd(':MEASURE:ITEM? VMAX,' + chnow,20)
                                chmeas = chmeas + '  VMAX:' + str(float(result))
                                result = self.Cmd(':MEASURE:ITEM:VMIN ' + chnow,20)
                                result = self.Cmd(':MEASURE:ITEM? VMIN,' + chnow,20)
                                chmeas = chmeas + '  VMIN:' + str(float(result))
                                result = self.Cmd(':MEASURE:ITEM:FREQ ' + chnow,20)
                                result = self.Cmd(':MEASURE:ITEM? FREQ,' + chnow,20)
                                chmeas = chmeas + '  FREQUENCY:' + str(float(result))
                        self.meas.append(chmeas)
                
        def Graph(self,channels):         

                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-' + str(self.sequence) + '-' + channels + '-' + now + self.outformat
		self.sequence += 1
                tu = 's'
                if self.timescale < 1e-6:
                        self.timescale = self.timescale * 1e9
                        tu = 'ns'
                elif self.timescale < 1e-3:
                        self.timescale = self.timescale * 1e6
                        tu = 'us'
                elif self.timescale < 1e-0:
                        self.timescale = self.timescale * 1e3
                        tu = 'ms'
                i = 1
                tics = '('
                while i < 11:
                        tics = tics + '("' + str(int(self.timescale*i)) + tu[0] + '") ' + str(i*100) + ',' 
                        i += 1
                tics = tics + '("' + str(int(self.timescale*i)) + tu[0] + '") ' + str(i*100) + ')' 
                        
                g = Gnuplot.Gnuplot()
                i = 0
                gdata=[]
                while channels != '':
                        print('-.')
                        channel = 'CHAN' + channels[0]
                        channels = channels[1:]
                        gdata.append(Gnuplot.Data(self.alldata[i],with_='lines',title=self.meas[i]))
                        i = i + 1

                g.title('Rigol DS1054')
                if self.outformat == '.svg':
                        g('set term svg size ' + self.size)
                else:
                        g('set term png size ' + self.size)
                g('set output \'' + fname + '\'')
                g('set key left')
                ymin = self.min_value - 0.1 * (self.max_value - self.min_value)
                ymax = self.max_value + 0.2 * (self.max_value - self.min_value)
                g('set yrange [' + str(ymin) + ':' + str(ymax) + ']')
                g('set xrange [0:1200]')
                g('set xtics ' + tics)
                g('set xlabel \' Time ' + str(self.timescale) + ' ' + tu  + ' per div\'')
                g('set ylabel \' Voltage in V\'')
                g('set grid')

                if self.outformat == ".svg":
                        g('set object 1 rect from screen 0, 0, 0 to screen 1, 1, 0 behind')
                        g('set object 1 rect fc  rgb "white"  fillstyle solid 1.0')
                        
                if i == 4:
                        g.plot(gdata[0],gdata[1],gdata[2],gdata[3])
                elif i == 3:
                        g.plot(gdata[0],gdata[1],gdata[2])
                elif i == 2:
                        g.plot(gdata[0],gdata[1])
                else:
                        g.plot(gdata[0])
                del g
                return str(fname + ' ')

        def RunOne(self, channels):
                self.Waveform(channels)
                self.Meas(channels)
                return self.Graph(channels)

        def Screendump(self):
                if self.screen == False:
                        return ' '
                result = self.Cmd(':DISPLAY:DATA?',300)[11:-3]
                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-' + str(self.sequence)+ '-screendump-' + now + '.bmp'
		self.sequence += 1
                newFile = open(fname, "wb")
                bindata=bytearray(result)
                newFile.write(bindata)
                newFile.close()
                return(fname + ' ')

        def ReadConfig(self,filename, need_exist):
                args=['dummy']
                try:
                        if filename[0] == '~':
                                filename = os.environ['HOME'] + filename[1:]
                        newFile = open(filename, "r") 
                except:
                        if need_exist:
                                print('config file ' + filename + ' not found')
                        return args
                all = newFile.read(1000000)
                newFile.close()
                lines = all.split('\n')
                for line in lines:
                        if len(line) > 0:
                                if line[0] != '#':
                                        args.append(line)
                return args
        
        def RunAll(self,cmdlineargs):

                orig = self.config
                preargs = self.ReadConfig(orig, False)
                s.ParseArgs(preargs)
                s.ParseArgs(cmdlineargs)
                
                if orig != self.config:
                        lastargs = self.ReadConfig(self.config, True)
                        s.ParseArgs(lastargs)

                if self.screen == False and len(self.leftargv) == 0:
                        self.Usage()

                if self.addr == '0.0.0.0':
                        self.Usage()

                st = vxi11.open(self.addr,self.device)
                if st != 0:
                   print('Could not connect to scope')
                   exit(0)
                   
                if self.nomodes == False:
                        if self.mode == 'RUN':
                                result = self.Cmd(':RUN',10)
                        if self.mode == 'STOP':
                                result = self.Cmd(':STOP',10)                        
                
                if self.screen == True:
                        file = self.Screendump()
                        if file != '':
                                self.files = self.files + file
                        
                for item in self.leftargv:
                        file = self.RunOne(item)
                        if file != '':
                                self.files = self.files + file

                if self.nomodes == False:
                        if self.after == 'RUN':
                                result = self.Cmd(':RUN',10)
                        if self.after == 'STOP':
                                result = self.Cmd(':STOP',10)                        

                st = vxi11.close(self.addr)
                
                if self.view == '':
                        print('')
                        print('Files created:' + self.files)
                else:
                        p = pexpect.spawn(self.view + ' ' + self.files)
                        p.wait()
                print('')
                        

s = scopeIO()
s.RunAll(sys.argv)
del s
