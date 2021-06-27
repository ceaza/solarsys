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
import logging

logger = logging.getLogger(__name__)


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
        qpigs_status_dict = {keys[i]:int(v) for i,v in enumerate(list(status))}
        return qpigs_status_dict
        


    def read_response(self,res,command):
        '''
        Decode the response from the Axpert
        '''
        send_dict = {}
        if command=='QPIGS':
            logger.debug('QPIGS result: %s',res)
            res = res[1:].split()
            if res[0][:3]=='NAK':
                send_dict['response']='NAK'
            else:
                try:
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
                except Exception as e:
                    logger.error(e)
                    send_dict['error'] = e
                
        elif command == 'QPIRI':
            res = res[1:].split()
            print(res)
            if len(res) < 10:
                send_dict['response']='NAK'
            else:
                try:
                    send_dict['grid_rating_voltage']=float(res[0]) # ["float", "AC Input Voltage", "V"],230
                    send_dict['grid_rating_current']=float(res[1])#  ["float", "AC Input Current", "A"],21.7
                    send_dict['out_rating_voltage']=float(res[2])# ["float", "AC Output Voltage", "V"],230
                    send_dict['out_rating_freq']=float(res[3])# ["float", "AC Output Frequency", "Hz"],50
                    send_dict['out_rating_current']=float(res[4])#  ["float", "AC Output Current", "A"],21.7
                    send_dict['out_rating_apparent_pwr']=float(res[5]) #  ["int", "AC Output Apparent Power", "VA"],5000
                    send_dict['out_rating_active_pwr']=float(res[6])#  ["int", "AC Output Active Power", "W"],5000
                    send_dict['bat_rating_voltage']=float(res[7])#  ["float", "Battery Voltage", "V"],48
                    send_dict['bat_recharge_voltage']=float(res[8])#  ["float", "Battery Recharge Voltage", "V"],48
                    send_dict['bat_under_voltage']=float(res[9])# ["float", "Battery Under Voltage", "V"],44
                    send_dict['bat_bulcharge_voltage']=float(res[10])##             ["float", "Battery Bulk Charge Voltage", "V"],54
                    send_dict['bat_floatcharge_voltage']=float(res[11])#  ["float", "Battery Float Charge Voltage", "V"],53.2
                    send_dict['bat_type']=int(res[12]) # 2
                    #  ["option", "Battery Type", ["AGM", "Flooded", "User", "TBD", "Pylontech", "WECO", "Soltaro", "LIb-protocol compatible", "3rd party Lithium"]],
                    send_dict['max_ac_change_current']=float(res[13])#  ["int", "Max AC Charging Current", "A"], 02
                    send_dict['max_charge_current']=float(res[14])#  ["int", "Max Charging Current", "A"],60
                    send_dict['input_voltage_range']=int(res[15])# ["option", "Input Voltage Range", ["Appliance", "UPS"]],0
                    send_dict['POP']=int(res[16])# 1            [
                            #                 "option",
                            #                 "Output Source Priority",
                            #                 ["Utility first", "Solar first", "SBU first"],
                            #             ],
                    send_dict['PCP']=int(res[17])#  2 [
                            #                 "option",
                            #                 "Charger Source Priority",
                            #                 [
                            #                     "Utility first",
                            #                     "Solar first",
                            #                     "Solar + Utility",
                            #                     "Only solar charging permitted",
                            #                 ],
                            #             ],
                    send_dict['max_parallel_units']=int(res[18])#        ["int", "Max Parallel Units", "units"],
                    send_dict['machine_type']=int(res[19])#             
                                #             [
                                #                 "keyed",
                                #                 "Machine Type",
                                #                 {"00": "Grid tie", "01": "Off Grid", "10": "Hybrid"},
                                #             ],
                    send_dict['topology'] = int(res[20])#             ["option", "Topology", ["transformerless", "transformer"]],
                    send_dict['output_mode'] = int(res[21])# #             [
                                #                 "option",
                                #                 "Output Mode",
                                #                 [
                                #                     "single machine output",
                                #                     "parallel output",
                                #                     "Phase 1 of 3 Phase output",
                                #                     "Phase 2 of 3 Phase output",
                                #                     "Phase 3 of 3 Phase output",
                                #                     "Phase 1 of 2 phase output",
                                #                     "Phase 2 of 2 phase output",
                                #                     "unknown output",
                                #                 ],
                                #             ],
                    send_dict['bat_redischarge_votage'] = float(res[22])#   ["float", "Battery Redischarge Voltage", "V"],
                    send_dict['pv_ok'] = int(res[23])#             [
                            #                 "option",
                            #                 "PV OK Condition",
                            #                 [
                            #                     "As long as one unit of inverters has connect PV, parallel system will consider PV OK",
                            #                     "Only All of inverters have connect PV, parallel system will consider PV OK",
                            #                 ],
                            #             ],
                    send_dict['pv_pwr_bal'] = int(res[24])#             [
                            #                 "option",
                            #                 "PV Power Balance",
                            #                 [
                            #                     "PV input max current will be the max charged current",
                            #                     "PV input max power will be the sum of the max charged power and loads power",
                            #                 ],
                            #             ],
                except Exception as e:
                    logger.error(e)
                    send_dict['error'] = e                
        elif command in ['POP00','POP01','POP02','PCP00','PCP01','PCP02','PCP03']:
            send_dict['response']='ACK'   
        return send_dict

    def submit_command_and_receive(self,command,non_block=False):
        if non_block:
            self.fd = os.open(self.device,os.O_RDWR | os.O_NONBLOCK)
        else:
            self.fd = os.open(self.device,os.O_RDWR)
            
        command = str.encode(command)
        print(command)
        crc = self.calc_crc(command)
        fcall = command + crc + b'\r'
        os.write(self.fd, fcall)
        time.sleep(0.35)
        response = b''
        while True:
            # print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            r = os.read(self.fd, 256)
            response += r
            if b'\r' in r: break
        os.close(self.fd)
        return response

    def run(self,command='QPIGS',non_block=False):
        res = self.submit_command_and_receive(command,non_block=non_block)
        print(res)
        send_dict = self.read_response(res,command)
        # if command=='QPIGS':
        #    self.send_all_data(send_dict)
        #else:
        #    print(res)
        return send_dict
            
    def send_and_receive(self,command) -> dict:
        '''
        From mpp_solar
        '''
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
            #log.debug("USB open error: {}".format(e))
            return {"ERROR": ["USB open error: {}".format(e), ""]}
        # Send the command to the open usb connection
        to_send = full_command
        try:
            pass
            #log.debug(f"length of to_send: {len(to_send)}")
        except:  # noqa: E722
            import pdb

            pdb.set_trace()
        if len(to_send) <= 8:
            # Send all at once
            #log.debug("1 chunk send")
            time.sleep(0.35)
            os.write(usb0, to_send)
        elif len(to_send) > 8 and len(to_send) < 11:
            #log.debug("2 chunk send")
            time.sleep(0.35)
            os.write(usb0, to_send[:5])
            time.sleep(0.35)
            os.write(usb0, to_send[5:])
        else:
            while len(to_send) > 0:
                #log.debug("multiple chunk send")
                # Split the byte command into smaller chucks
                send, to_send = to_send[:8], to_send[8:]
                #log.debug("send: {}, to_send: {}".format(send, to_send))
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
                pass
                #log.debug("USB read error: {}".format(e))
            # Finished is \r is in byte_response
            if bytes([13]) in response_line:
                # remove anything after the \r
                response_line = response_line[: response_line.find(bytes([13])) + 1]
                break
        #log.debug("usb response was: %s", response_line)
        os.close(usb0)
        return response_line         
            

if __name__ == '__main__':
    axpert = Axpert()
    #print(axpert.send_and_receive('POP02'))
    output = axpert.run(command='QPIGS')
    print(output)
    status  = axpert.run(command='QPIRI')
    print(type(status['POP']))
    print(status)
    # axpert.run(command='POP02')
