#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2013 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Crazyflie ablock is used to receive characters sent using ablock
from the firmware.
"""

__author__ = 'Bitcraze AB'
__all__ = ['Ablock']

import time
import struct
from cflib.utils.callbacks import Caller
from cflib.crtp.crtpstack import CRTPPacket, CRTPPort
from PyQt4.QtCore import pyqtSlot, pyqtSignal

import urllib2
import datetime
import math


class Ablock:
    """
    Crazyflie ablock is used to receive characters sent using ablock
    from the firmware.
    """
    
    receivedChar = Caller()
    
    def __init__(self, crazyflie):
        """
        Initialize the ablock and register it to receive data from the copter.
        """
        self.cf = crazyflie
        self.cf.add_port_callback(CRTPPort.ABLOCK, self.incoming)
        self.init_gps = 0
        self.active = False

        self.taccs = 60.0
        self.lat = 33.767440
        self.lon = -117.500734
        self.altmsl = 382.0
        self.gh = -32.5
        self.pacc = 150.0

    def incoming(self, packet):
        """
        Callback for data received from the firmware
          <S> Begin AssistNow       input
          <n> Ready for Next Line   input
          <r> Repeat Last Line      input
          <R> Repeat Last Block     input
          <E> End of AssistNow      input

          <G> Go Ahead              output
          <E> End of Data           output
          <X> Abort AssistNow       output   
        """
        # This might be done prettier ;-)
        ablock_text = "%s" % struct.unpack("%is" % len(packet.data),
                                            packet.data)
        self.receivedChar.call(ablock_text)

#        size = len(ablock_text)       
#        print ("insize %d" % size)
        print ("indata %s" % ablock_text)

        """Begin AssistNow Transfers"""
        if ablock_text == "<S>\n":
            if self.init_gps == 0 :
                self.receivedChar.call("Reset Gps\n")
                self.rst_hex(False)
            if self.init_gps == 1 :
                self.receivedChar.call("Nav_Pvt Enable\n")
                self.pvt_hex(False)
            if self.init_gps == 2 :
                self.receivedChar.call("NMEA Disable\n")
                self.ebx_hex(False)
            if self.init_gps == 3 :
                self.receivedChar.call("Time_UTC\n")
                self.utc_hex(self.taccs, False)
            if self.init_gps == 4 :
                self.receivedChar.call("Pos_LLH\n")
                self.llh_hex(self.lat, self.lon, self.altmsl, self.gh, self.pacc, False)
            if self.init_gps == 5 :
                self.receivedChar.call("Alm\n")
                msg = "B5620611020008002191"
                self.fileFormat(msg, False)
                self.sv_alm_hex(True)
            if self.init_gps > 5 :
                if self.init_gps == 99 :
                    self.receivedChar.call("AssistNow Aborted\n")
                else:
                    self.receivedChar.call("Finished\n")
                    self.outgoing("<E>\n")
                self.init_gps = 0                
            else:
                self.init_gps += 1 
                self.loadlines()                
                self.endBlock = True
                self.lineNbr = -1
                self.active = True
                self.outgoing("<G>\n")
        elif (self.active):
            if (ablock_text == "<n>\n"):   
                self.lineNbr +=1
                line = self.lines[self.lineNbr]
                if (self.endBlock):
                    self.blockNbr = self.lineNbr
                    endBlock = False
                size = len(line)
                if (size == 0):
                    self.active = False                   
                    self.outgoing("<E>\n")
                    self.receivedChar.call("EOM\n")
                elif (size > 29):
                    self.active = False
                    self.init_gps = 99
                    self.outgoing("<X>\n")
                    self.receivedChar.call("EOM\n")
                elif ((line[size-2] == "<") and (line[size-1] == ">")):           
                    self.endBlock = True
                    self.outgoing("%s\n" % line)
                else:
                    print ("line %d" %self.lineNbr) 
                    self.outgoing("%s\n" % line)    
            elif (ablock_text == "<r>\n"): 
                print "<r>\n"
                line = self.lines[self.lineNbr]
                self.outgoing("%s\n" % line)
            elif (ablock_text == "<R>\n"): 
                print "<R>\n"
                endBlock = False
                self.lineNbr = self.blockNbr
                line = self.lines[self.lineNbr]
                self.outgoing("%s\n" % line)
            elif (ablock_text == "<X>\n"): 
                print "<X>\n"
                self.active = False
                self.receivedChar.call("EOM\n")
                self.init_gps = 99
            elif (ablock_text == "<E>\n"): 
                self.active = False
                self.receivedChar.call("EOM\n")
        else:
            self.active = False
            self.init_gps = 99
            self.outgoing("<X>\n")

    def loadlines(self):
        with open("a-block.txt", "r") as mfile:
            data = mfile.read()
        mfile.closed
        self.lines = data.splitlines()
        self.lines.append("");    

    def outgoing(self, p):
        time.sleep(100.0 / 1000.0)
        pk = CRTPPacket()
        pk.port = CRTPPort.ABLOCK
        pk.data = p
        self.cf.send_packet(pk)

    def putFile(self, data, add):
        if add :           
            with open("a-block.txt", "a") as mfile:
                 mfile.write(data)
            mfile.closed    
        else:
            with open("a-block.txt", "w") as mfile:
                 mfile.write(data) 
            mfile.closed 

    def fileFormat(self, data, add):
        block = ""
        lineLen = 28
        dataLen = len(data)
        nbrFull = dataLen / lineLen
        lenLast = dataLen % lineLen
        if lenLast > lineLen - 2 :
            nbrFull -= 1
        iData = 0
        while nbrFull > 0 :
            i = 0
            while i < lineLen :
                block = block + data[iData]
                iData += 1
                i += 1 
            block = block + "\n"
            nbrFull -= 1
        lenNext = 0
        if lenLast > lineLen - 2 :
            lenNext = lineLen - 2
        i = 0
        while i < lenNext :
            block = block + data[iData]
            iData += 1
            i += 1
        if lenNext > 0 :
            block = block + "\n"
        lenLast -= lenNext
        i = 0
        while i < lenLast :
            block = block + data[iData]
            iData += 1
            i += 1
        block = block + "<>\n"
        print len(block)
        self.putFile(block, add)

    def get_int_len(self, val, base):
        value = val
        if value < 0:
            value = - value
        l = 1
        while value > base - 1:
            l += 1
            value /= base
        return l

    def itoa(self, decimal, base, precision):
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        data  = []
        i = 1
        len = 0
        n = decimal
        numLen = self.get_int_len(decimal, base)
        fillZero = 0
        minusPrecision = 0
        if (decimal < 0 and base == 10):
            n = -decimal
            data.append("-")
        else:
            if decimal < 0 :
                minusPrecision = precision
                while base**minusPrecision + decimal <= 0 :
                   minusPrecision += 1 
                n = base**minusPrecision + decimal
                numLen = self.get_int_len(n, base)
#                print n
        if (numLen < precision):
            fillZero = precision - numLen
            while fillZero > 0:
                data.append("0")
                fillZero -= 1
        while n / i:
            i *= base
        if n == 0:
            i = base
        while i / base :
            i /= base
            data.append(digits[(n / i) % base])
            len += 1
        return data

    def listToString(self, list1):
        return str(list1).replace('[','').replace(']','').replace(',','').replace("'",'').replace(' ','')

    def cksum(self, msg, len):
        cka = 0
        ckb = 0
        if len > 0 :
            i = 4
            while i < len :
                vala = int(msg[i], 16)
                vala -= 48
                if vala > 9 :
                    vala -= 7
                valb = int(msg[i+1], 16)
                valb -= 48
                if valb > 9 :
                    valb -= 7             
                cka = cka + (vala * 16) + (valb & 15)
                ckb += cka
                i += 2
        cka = cka % 256
        ckb = ckb % 256
        return cka, ckb

    def append_0(self, msg, nbr):
        msg.append(self.itoa(0, 16, nbr))
        return msg

    def append_2(self, msg, int_val):
        msg.append(self.itoa(int_val, 16, 2))
        return msg

    def append_4(self, msg, int_val):
        x = self.itoa(int_val, 16, 4)
        msg.append(x[2:])
        msg.append(x[:-2])
        return msg

    def append_8(self, msg, int_val):
        x = self.itoa(int_val, 16, 8)
        msg.append(x[6:])
        msg.append(x[4:-2])
        msg.append(x[2:-4])
        msg.append(x[:-6])
        return msg

    def ini_utc(self, hdr, taccs):
        msg = []
        today = datetime.datetime.utcnow()
        msg.append(hdr)
        msg = self.append_4(msg, int(today.year))
        msg = self.append_2(msg, int(today.month))
        msg = self.append_2(msg, int(today.day))
        msg = self.append_2(msg, int(today.hour))
        msg = self.append_2(msg, int(today.minute))
        msg = self.append_2(msg, int(today.second))
        msg = self.append_0(msg, 10)
        msg = self.append_4(msg, int(taccs))
        msg = self.append_0(msg, 12)   
#        print msg
        return msg

    def ini_llh(self, hdr, lat, lon, alt, gh, pacc):
        msg = []
        msg.append(hdr)
        msg = self.append_8(msg, int(round(lat * 10000000.0)))
        msg = self.append_8(msg, int(round(lon * 10000000.0)))
        msg = self.append_8(msg, int(round((alt + gh) * 100.0)))
        msg = self.append_8(msg, int(round(pacc * 100.0)))    
#        print msg
        return msg

    def alm_load(self):   
        today = datetime.datetime.now()
        dayNbr = (today - datetime.datetime(today.year, 1, 1)).days + 1
#        print dayNbr
#        print
        data = urllib2.urlopen("http://www.navcen.uscg.gov/?Do=getAlmanac&almanac=%d" % dayNbr).read(20000)
        data = data.split("\n")
        return data

    def isfloat(self, value):
        try:
            val = float(value)    
            return val 
        except ValueError:
            print("Bad Value")
            return 0.0

    def isIndex(self, data, i):
        try:
            line = data[i]    
            return line 
        except IndexError:
            line = "*********************************************\n"
            return line

    def ini_alm(self, data, i, hdr):
        msg = []
        eod = 0
        mI = 55.0 * math.pi / 180.0
        line = self.isIndex(data, i)
        if (line[18:-21] == "almanac"):
            i += 1
            line = data[i]
            svId = line[25:-1]    
            svId = int(round(self.isfloat(svId)))
#            print(svId)
            i += 1
            line = data[i]
            svHealth = line[25:-1]   
            svHealth = int(round(self.isfloat(svHealth)))
#            print(svHealth)
            i += 1
            line = data[i]
            e = line[25:-1]
#            print(e)
            e = int(round(self.isfloat(e) * 2**21))
#            print(e)
            i += 1
            line = data[i]
            toa = line[25:-1]
#            print(toa)
            toa = int(round(self.isfloat(toa) * 2**-12))
#            print(toa)
            i += 1
            line = data[i]
            deltaI = line[25:-1]
#            print(deltaI)
            deltaI = int(round((self.isfloat(deltaI) - mI) / math.pi * 2**19))
#            print(deltaI)
            i += 1
            line = data[i]
            omegaDot = line[25:-1]    
            omegaDot = int(round(self.isfloat(omegaDot) / math.pi * 2**38))
#            print(omegaDot)
            i += 1
            line = data[i]
            sqrtA = line[25:-1]    
            sqrtA = int(round(self.isfloat(sqrtA) * 2**11))
#            print(sqrtA)
            i += 1
            line = data[i]
            omega0 = line[25:-1]    
            omega0 = int(round(self.isfloat(omega0) / math.pi * 2**23))
#            print(omega0)
            i += 1
            line = data[i]
            omega = line[25:-1]    
            omega = int(round(self.isfloat(omega) / math.pi * 2**23))
#            print(omega)
            i += 1
            line = data[i]
            mo = line[25:-1]    
            mo = int(round(self.isfloat(mo) / math.pi * 2**23))
#            print(mo)
            i += 1
            line = data[i]
            af0 = line[25:-1]    
            af0 = int(round(self.isfloat(af0) * 2**20))
#            print(af0)
            i += 1
            line = data[i]
            af1 = line[25:-1]    
            af1 = int(round(self.isfloat(af1) * 2**38))
#            print(af1)
            i += 1
            line = data[i]
            almWNa = line[25:-1]    
            almWNa = int(round(self.isfloat(almWNa)))
            almWNa = almWNa % 256
#            print(almWNa)
            i += 2
        else:
            print("End of SV Alm Data")
            eod = 1    
        if eod == 0 :
            msg.append(hdr)
            msg = self.append_2(msg, svId)
            msg = self.append_2(msg, svHealth)
            msg = self.append_4(msg, e)
            msg = self.append_2(msg, almWNa)
            msg = self.append_2(msg, toa)
            msg = self.append_4(msg, deltaI)
            msg = self.append_4(msg, omegaDot)
            msg = self.append_8(msg, sqrtA)
            msg = self.append_8(msg, omega0)
            msg = self.append_8(msg, omega)
            msg = self.append_8(msg, mo)
            msg = self.append_4(msg, af0)
            msg = self.append_4(msg, af1)
            msg = self.append_0(msg, 8) 
            print "G", svId
        return eod, i, msg
 
    def rst_hex(self, add):
        msg = "B56206040400FFB90100C78D"
        self.fileFormat(msg, add)

    def pvt_hex(self, add):
        msg = "B56206010800010700010000000018E1"
        self.fileFormat(msg, add)

    def ebx_hex(self, add):
        msg = "B5620600140001000000D0080000802500000700010000000000A0A9"
        self.fileFormat(msg, add)

    def out_hex(self, msg_list, add):
        msg_str = self.listToString(msg_list)
        len_str = len(msg_str)
        cka, ckb = self.cksum(msg_str, len_str)
        msg = msg_str + self.listToString(self.itoa(cka, 16, 2) + self.itoa(ckb, 16, 2))
#        print len(msg)
#        for z in msg:
#            print z,
#        print
        self.fileFormat(msg, add)

    def utc_hex(self, taccs, add):
        utc_Hdr = "B5621340180010000080"
        msg_list = self.ini_utc(utc_Hdr, taccs)
        self.out_hex(msg_list, add)

    def llh_hex(self, lat, lon, alt, gh, pacc, add):
        llh_Hdr = "B5621340140001000000"
        msg_list = self.ini_llh(llh_Hdr, lat, lon, alt, gh, pacc)
        self.out_hex(msg_list, add) 

    def alm_hex(self, indx_sv_list, add):
        sv_Hdr = "B562130024000200"
        data = self.alm_load()
        eod, i_list, msg_list = self.ini_alm(data,indx_sv_list,sv_Hdr)
        if eod == 0:
#            print msg_list 
#            print len(msg_list)
            self.out_hex(msg_list, add)
        return eod, i_list

    def sv_alm_hex(self, add):
        indx_sv_list = 0
        j = 0
        while j < 32 :
            j += 1
            eod, indx_sv_list = self.alm_hex(indx_sv_list, add)
            if eod != 0 :
                break
#        msg = "B5620611020008002191"
#        self.fileFormat(msg, True)
    
