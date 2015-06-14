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

import vxi11conn

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

	def Info(self, text):
		print('measurement' + str(self.sequence) + ':INFO: ' + text)
	def Error(self,text):
		print('measurement' + str(self.sequence) + ':ERROR: ' + text)

        def Waveform(self, channels):
		self.Info('getting waveforms')
                self.alldata = []
                self.rigol.command(':WAVEFORM:FORMAT ASCII')
                self.rigol.command(':WAVEFORM:POINT:MODE NORMAL')
                self.timescale = float(self.rigol.command(':TIMEBASE:MAIN:SCALE?'))
                self.min_value = 1e10
                self.max_value = -1e10
                while channels != '':
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
                        self.rigol.command(':WAVEFORM:SOURCE ' + chnow)
                        data = self.rigol.command(':WAVEFORM:DATA?',10000)[11:-3]
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

	def OneMeas(self,channel,meas):
        	self.rigol.command(':MEASURE:ITEM:' + meas + ' ' + channel)
		resp = float(self.rigol.command(':MEASURE:ITEM? ' + meas + ',' + channel))
                return '  ' + meas + '=' + str(resp).format('%.2G')
		
        def Meas(self, channels):
		self.Info('getting measurements');
                self.meas=[]
                while channels != '':
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
                        chmeas = chnow
                        if self.nomeas == False:
				chmeas = chmeas + self.OneMeas(chnow, 'VPP')
				chmeas = chmeas + self.OneMeas(chnow, 'VMAX')
				chmeas = chmeas + self.OneMeas(chnow, 'VMIN')
				chmeas = chmeas + self.OneMeas(chnow, 'FREQUENCY')
                        self.meas.append(chmeas)
                
        def Graph(self,channels):         
		self.Info('making graph')
                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-' + str(self.sequence) + '-' + channels + '-' + now + self.outformat
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
		self.Info('started')
		onchannels=''
                while channels != '':
                        chnow = 'CHAN' + channels[0]
                        channels = channels[1:]
			online = self.rigol.command(':' + chnow + ':DISPLAY?')[0]
			if online != '1':
				self.Error(chnow + ' offline, skipping channel')
			else:
				onchannels = onchannels + chnow[4:]
		if onchannels == '':
			self.Error('no channels online, skipping')
			self.sequence += 1
			return ''		
                self.Waveform(onchannels)
                self.Meas(onchannels)
                ret = self.Graph(onchannels)
		self.Info('finished')
		self.sequence += 1
		return ret

        def Screendump(self):
                if self.screen == False:
                        return ' '
		self.Info('started screendump, this takes many seconds')
                now = time.strftime('%d.%m.%Y-%H.%M.%S')
                fname = self.prefix + '-' + str(self.sequence)+ '-screendump-' + now + '.bmp'
                bindata = self.rigol.command(':DISPLAY:DATA?',30000,'BIN')[11:-3]
                newFile = open(fname, "wb")
                newFile.write(bindata)
                newFile.close()
		self.Info('screendump finished')
		self.sequence += 1
                return fname + ' '

        def ReadConfig(self,filename, need_exist):
                args=['dummy']
                try:
                        if filename[0] == '~':
                                filename = os.environ['HOME'] + filename[1:]
                        newFile = open(filename, "r") 
                except:
                        if need_exist:
                                self.Error('config file ' + filename + ' not found')
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

		self.rigol = vxi11conn.conn()
                if not self.rigol.connect(self.addr,4000000,self.device):
                   self.Info('Could not connect to scope')
                   return
                   
                if self.nomodes == False and self.mode != '':
			self.Info('set scope during capture mode to ' + self.mode)
                        self.rigol.command(':'+self.mode)

                if self.screen == True:
                        file = self.Screendump()
                        if file != '':
                                self.files = self.files + file
                        
                for item in self.leftargv:
                        file = self.RunOne(item)
                        if file != '':
                                self.files = self.files + file

                if self.nomodes == False and self.after != '':
			self.Info('set scope after capture mode to ' + self.after)
                        self.rigol.command(':' + self.after)

                self.rigol.disconnect()
		del self.rigol
                
		if self.view != '':
			try:
                	      	p = pexpect.spawn(self.view + ' ' + self.files)
			except:
				self.Info('could not start ',self.view)
				return
			else:
				try:
					p.wait()
				except:
					return
			return
		print('Files created:' + self.files)

s = scopeIO()
s.RunAll(sys.argv)
del s
