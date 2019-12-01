#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 12:44:36 2019

@author: charles
"""
import time
import os, sys
import crcmod
from crc16 import crc16xmodem

xmodem_crc_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

def calc_crc(command):
    global crc
    crc = xmodem_crc_func(command)
    crc =crc.to_bytes(2,byteorder='big')
    return crc

command = b'QPIGS'
crc = calc_crc(command)


fd = os.open("/dev/hidraw0", os.O_RDWR)
os.write(fd, b"QPI\xBE\xAC\r")
print(os.read(fd, 512))

fcall = command + crc + b'\r'

#fcall = b'QPIGS\xA9\xB7\r'
fd = os.open("/dev/hidraw0", os.O_RDWR)


# QPIGS call
for n in range(0,10):
    os.write(fd, fcall)
    response = b''
    while True:
        r = os.read(fd, 256)
        response += r
        if b'\r' in r: break
    print(response[1:-5].split())
