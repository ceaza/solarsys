#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 12:44:36 2019
@author: charles
"""
import time
import os, sys
import crcmod
import json
from crc16 import crc16xmodem

apikey = "5501428544958e9fc4827004e36922e4"
server = 'centurionsolar.co.za'
emoncmspath ='emoncms11'

import http.client as httplib
def send_data(data):
    conn = httplib.HTTPConnection(server)
    string = "/"+emoncmspath+"/input/post.json?&node="+"Raspberry"+"&json="+data+"&apikey="+apikey
    print(string)
    conn.request("GET",string)
    response = conn.getresponse()
    print(response)
    conn.close()

def send_all_data(ddict):
    keys_to_send = ['pvw atts','gri dvoltage']
    sdict = {} 
    for k,v in ddict.items():
        if k not in keys_to_send:
            sdict['{}'.format(k)] = v
    data = json.dumps(sdict)
    data = data.replace('"','')
    data = data.replace(' ','')
    print(data)
    try:
        send_data(data)
    except:
        print('timed out')

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
while True:
    os.write(fd, fcall)
    response = b''
    while True:
        r = os.read(fd, 256)
        response += r
        if b'\r' in r: break
    res = response[1:].split()
    print(res)
    send_dict = {}
    send_dict['gridvoltage']=float(res[0])	
    send_dict['grid_frequency']=float(res[1])
    send_dict['inverter_voltage']=float(res[2])
    send_dict['inverter_frequency']=float(res[3])
    send_dict['apparent_power']=float(res[4]) # AC output apparent power
    send_dict['loadwatts']=float(res[5]) # AC output active power
    send_dict['loadpercentage']=float(res[6]) # Ouput load percent
    send_dict['busvoltage']=float(res[7]) # BUS votage
    send_dict['batteryvolts']=float(res[8]) # Battery voltage
    send_dict['bat_charge_current']=float(res[9]) # Battery changing current
    send_dict['soc']=float(res[10]) # SOC voltage infered
    send_dict['inverter_temp']=float(res[11]) # Inverter temp
    send_dict['pv_input_current_battery']=float(res[12]) # PV input current for battery

    send_dict['pvVolts1']=float(res[13]) # PV input voltage
    # 14 Battery voltage from SCC
    send_dict['bat_discharge_current']=float(res[15]) # Battery discharge current
    # send_dict['device_status']=float(res[16]) # Device status
    # host of stutus flags
    # send_dict['battery_volts_for_fans']=float(res[17]) # Battery voltage offset for fans on
    #send_dict['eeprom_version']=float(res[18]) # EEPROM version
    send_dict['pvwatts']=float(res[19]) # pv watts
    send_dict['batteryamps'] = send_dict['bat_charge_current'] - send_dict['bat_discharge_current']
    send_dict['batterywatts'] = send_dict['batteryamps'] * send_dict['batteryvolts']
    send_dict['pvAmps1'] = send_dict['pv_input_current_battery']
    
    send_dict['gridwatts'] = 0.0 if send_dict['batterywatts']< 0.0 \
                             else send_dict['loadwatts'] + send_dict['batterywatts'] - send_dict['pvwatts']
    send_dict['SolarWatts'] = send_dict['loadwatts'] - send_dict['gridwatts']
    print(res[19])
    send_all_data(send_dict)


'''
solar_watts
grid_watts
battery_watts
pv_watts
ac_apparent_power
ac_active_power
gridwatts = loadwatts-battery_watts-pv_watts

'''

