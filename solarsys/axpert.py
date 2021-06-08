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
import http.client as httplib
import logging as log


class Axpert:
    apikey = "5501428544958e9fc4827004e36922e4"
    emon_server = 'centurionsolar.co.za'
    emoncmspath ='emoncms11'
    #xmodem_crc_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

    def __init__(self,device='/dev/hidraw0'):
        self.device = device
        self.xmodem_crc_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
        # self.fd = os.open(device,os.O_RDWR)

    def send_data(self,data):
        conn = httplib.HTTPConnection(self.emon_server,timeout=5)
        string = "/"+self.emoncmspath+"/input/post.json?&node="+"Raspberry"+"&json="+data+"&apikey="+ self.apikey
        #print(string)
        conn.request("GET",string)
        response = conn.getresponse()
        print(response)
        conn.close()

    def send_all_data(self,ddict):
        keys_to_send = ['device_status','pvw atts','gri dvoltage']
        sdict = {} 
        for k,v in ddict.items():
            if k not in keys_to_send:
                sdict['{}'.format(k)] = v
        data = json.dumps(sdict)
        data = data.replace('"','')
        data = data.replace(' ','')
        # print(data)
        try:
            self.send_data(data)
        except:
            print('timed out')

    def calc_crc(self,command):
        crc = self.xmodem_crc_func(command)
        crc =crc.to_bytes(2,byteorder='big')
        return crc

    def qpigs_status(self,status):
        '''
            "Is SBU Priority Version Added",
            "Is Configuration Changed",
            "Is SCC Firmware Updated",
            "Is Load On",
            "Is Battery Voltage to Steady While Charging",
            "Is Charging On",
            "Is SCC Charging On",
            "Is AC Charging On",
        '''
        keys = ['SBU_priority','config_changed','SSC_firmware_updated',
                'load_on','bat_volt_steady','charging_on','scc_changing_on',
                'ac_on']
        qpigs_status_dict = {keys[i]:v for i,v in enumerate(list(status))}
        return qpigs_status_dict
        


    def read_response(self,res,command):
        '''
        Decode the response from the Axpert
        '''
        send_dict = {}
        if command=='QPIGS':
            res = res[1:].split()
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
            send_dict['device_status']= self.qpigs_status(res[16].decode("utf-8")) # Device status
            # host of stutus flags
            # send_dict['battery_volts_for_fans']=float(res[17]) # Battery voltage offset for fans on
            #send_dict['eeprom_version']=float(res[18]) # EEPROM version
            send_dict['pvwatts']=float(res[19]) # pv watts
            send_dict['batteryamps'] = send_dict['bat_charge_current'] - send_dict['bat_discharge_current']
            send_dict['batterywatts'] = send_dict['batteryamps'] * send_dict['batteryvolts']
            send_dict['pvAmps1'] = send_dict['pv_input_current_battery']
            
            send_dict['gridwatts'] = send_dict['loadwatts'] + send_dict['batterywatts'] - send_dict['pvwatts']
            send_dict['gridwatts'] = 0.0 if send_dict['gridwatts'] < 0.0 \
                                    else send_dict['gridwatts']
            send_dict['SolarWatts'] = send_dict['loadwatts'] - send_dict['gridwatts']
        elif command in ['POP00','POP01','POP02','PCP00','PCP01','PCP02','PCP03']:
            send_dict['ACK'] = res
                         
            
        return send_dict

    def submit_command_and_receive(self,command):
        self.fd = os.open(self.device,os.O_RDWR)
        command = str.encode(command)
        print(command)
        crc = self.calc_crc(command)
        fcall = command + crc + b'\r'
        os.write(self.fd, fcall)
        time.sleep(0.35)
        response = b''
        while True:
            r = os.read(self.fd, 256)
            response += r
            if b'\r' in r: break
        os.close(self.fd)
        return response

    def run(self,command='QPIGS'):
        res = self.submit_command_and_receive(command)
        send_dict = self.read_response(res,command)
        if command=='QPIGS':
            self.send_all_data(send_dict)
        else:
            print(res)
        return send_dict
            
    def send_and_receive(self,command) -> dict:
        # command = 'QPIGS'
        command = str.encode(command)
        print(command)
        crc = self.calc_crc(command)
        fcall = command + crc + b'\r'
        full_command = fcall 
        response_line = bytes()
        usb0 = None
        try:
            usb0 = os.open(self.device, os.O_RDWR | os.O_NONBLOCK)
        except Exception as e:
            log.debug("USB open error: {}".format(e))
            return {"ERROR": ["USB open error: {}".format(e), ""]}
        # Send the command to the open usb connection
        to_send = full_command
        try:
            log.debug(f"length of to_send: {len(to_send)}")
        except:  # noqa: E722
            import pdb

            pdb.set_trace()
        if len(to_send) <= 8:
            # Send all at once
            log.debug("1 chunk send")
            time.sleep(0.35)
            os.write(usb0, to_send)
        elif len(to_send) > 8 and len(to_send) < 11:
            log.debug("2 chunk send")
            time.sleep(0.35)
            os.write(usb0, to_send[:5])
            time.sleep(0.35)
            os.write(usb0, to_send[5:])
        else:
            while len(to_send) > 0:
                log.debug("multiple chunk send")
                # Split the byte command into smaller chucks
                send, to_send = to_send[:8], to_send[8:]
                log.debug("send: {}, to_send: {}".format(send, to_send))
                time.sleep(0.35)
                os.write(usb0, send)
        time.sleep(0.25)
        # Read from the usb connection
        # try to a max of 100 times
        for x in range(100):
            # attempt to deal with resource busy and other failures to read
            try:
                time.sleep(0.15)
                r = os.read(usb0, 256)
                response_line += r
            except Exception as e:
                log.debug("USB read error: {}".format(e))
            # Finished is \r is in byte_response
            if bytes([13]) in response_line:
                # remove anything after the \r
                response_line = response_line[: response_line.find(bytes([13])) + 1]
                break
        log.debug("usb response was: %s", response_line)
        os.close(usb0)
        return response_line         
            

if __name__ == '__main__':
    axpert = Axpert()
    print(axpert.send_and_receive('POP00'))
    output = axpert.run(command='QPIGS')
    print(output)
    #axpert.run(command='QPIRI')
    # axpert.run(command='POP02')
