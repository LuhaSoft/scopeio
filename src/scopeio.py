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

class scopeIO():

        def __init__(self):
                self.prefix = 'scope'
                self.nomeas = False
                self.view   = ''
                self.screen = False
                self.outformat = '.png'
                self.leftargv = []
                self.files = ''
                self.timescale = 1.0
                self.config = '~/.scopeio'
                self.addr = '0.0.0.0'
                # device needed for vxi11_cmd.cc special handling
                self.device = 'Rigol_DS1054'
                
        def Usage(self):
                print('Usage: scopeio.py [--help] [--nomeas] [--prefix=namestart] [--view=program] [--format=<fmt>] [--screen] [--noscreen] [--addr=a.b.c.d] [--config=filename] channels [channels] ... [channels]')
                print('Default prefix is scope')
                print('Formats supported now: png (default) and svg') 
                print('Examples:')
                print('  scope --nomeas --view=mirage 1           -- channel1 shown in mirage with no measurements (faster)')
                print('  scope 12 34 13 23  --prefix=myfile       -- ch1/ch2 ch3/ch4 ch1/ch3 ch3/ch4 images done in png with measurements')
                print('  scope --view=gimp 1234 --format=svg      -- all 4 channels in svg and send to gimp')
                print('  scope --screen                           --- take only display screen dump')
                print('  scope --screen 12                        --- take screen dump and two channel graph')
                print('  scope --addr=192.168.1.100 1 --noscreen  --- scope ip address set, no screen capture even when config file has screen on')
                print('  scope --config=~/.scopeio.myconfig       --- alternate config file, default is ~/.scopeio')
                print('')
                print('There can also be config file ~/.scopeio with all the settings, one per line with command line syntax')
                
                exit(0)

        def ParseArgs(self, argv):
                for item in argv[1:]:
                        if item == '--nomeas':
                                self.nomeas = True
                        elif item == '--help':
                                self.Usage()
                        elif item[0:7] == '--view=':
                                self.view = item[7:]
                        elif item[0:7] == '--addr=':
                                self.addr = item[7:]
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

        def WaitPrompt(self,waittime):
                try:
                        self.p.expect('Input command or query .*:', timeout=waittime)
                except:
                        print('Prompt wait timeout')
                
        def Cmd(self,cmd,waittime):
                cmd = cmd + '\n'
                sys.stdout.write('-')
                sys.stdout.flush()
                try:
                        self.p.writelines(cmd)
                except:
                        return 'Write timeout:' + cmd
                self.WaitPrompt(waittime)
                sys.stdout.write('.')
                sys.stdout.flush()
                #print(self.p.before)
                return self.p.before

        def Waveform(self, channels):
                self.alldata= []
                print('')
                result = self.Cmd(':WAVEFORM:FORMAT ASCII', 20)
                result = self.Cmd(':WAVEFORM:POINT:MODE NORMAL', 20)
                result = self.Cmd(':TIMEBASE:MAIN:SCALE?', 20)
                self.timescale = float(result[24:])
                while channels != '':
                        print('')
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
                        result = self.Cmd(':WAVEFORM:SOURCE ' + chnow,20)
                        data = self.Cmd(':WAVEFORM:DATA?',180)
                        data = data[29:-3]
                        data = data.split(',')
                        fdata = []
                        for item in data:
                                fdata.append(float(item))
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
                                #time.sleep(0.1)
                                result = self.Cmd(':MEASURE:ITEM? VPP,' + chnow,20)
                                chmeas = chmeas + '  VPP:' + str(float(result[25:-3]))
                                result = self.Cmd(':MEASURE:ITEM:VMAX ' + chnow,20)
                                #time.sleep(0.1)
                                result = self.Cmd(':MEASURE:ITEM? VMAX,' + chnow,20)
                                chmeas = chmeas + '  VMAX:' + str(float(result[26:-3]))
                                result = self.Cmd(':MEASURE:ITEM:VMIN ' + chnow,20)
                                #time.sleep(0.1)
                                result = self.Cmd(':MEASURE:ITEM? VMIN,' + chnow,20)
                                chmeas = chmeas + '  VMIN:' + str(float(result[26:-4]))
                                result = self.Cmd(':MEASURE:ITEM:FREQ ' + chnow,20)
                                #time.sleep(0.1)
                                result = self.Cmd(':MEASURE:ITEM? FREQ,' + chnow,20)
                                chmeas = chmeas + '  FREQUENCY:' + str(float(result[26:-4]))
                        self.meas.append(chmeas)
                
        def Graph(self,channels):         

                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-' + channels + '-' + now + self.outformat
                tu = 's'
                if self.timescale < 0.001:
                        self.timescale = self.timescale * 1000
                        tu = 'ms'
                elif self.timescale < 0.000001:
                        self.timescale = self.timescale * 1000000
                        tu = 'us'
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
                        g('set term svg size 1800,900')
                else:
                        g('set term png size 1800,900')
                g('set output \'' + fname + '\'')
                g('set key left')
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
                result = self.Cmd(':STOP',20)
                self.Waveform(channels)
                self.Meas(channels)
                result = self.Cmd(':RUN',20)
                return self.Graph(channels)

        def Screendump(self):
                if self.screen == False:
                        return ' '
                result = self.Cmd(':DISPLAY:DATA?',180)
                i = 0
                ch = ''
                while ch != '#':
                        ch = result[i]
                        i = i + 1
                        if i > 100:
                                print('screendump not found')
                                return('')
                if result[i] != '9':
                        print('screendump not found')
                        return('')
                datalen = int(result[i+1:i+10],10)
                if datalen != 1152054:
                        print('screendump size wrong')
                        return('')
                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-screendump-' + now + '.bmp'
                newFile = open(fname, "wb")
                j = 0;
                datalen -= 8
                bindata=bytearray()
                while j < datalen*2:
                        hexval = result[j+i+10:j+i+12]
                        value = int(hexval, 16)
                        bindata.append(value & 0xff)
                        j += 2
                # some data is lost according convert program, replace with zeros
                j = 0
                while j < 8:
                        bindata.append(0)
                        j += 1
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
                        
                self.p = pexpect.spawn('vxi11_cmd ' + self.addr + ' ' +  self.device)
                self.WaitPrompt(20)

                if self.screen == True:
                        file = self.Screendump()
                        if file != '':
                                self.files = self.files + file
                        
                for item in self.leftargv:
                        file = self.RunOne(item)
                        if file != '':
                                self.files = self.files + file

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
