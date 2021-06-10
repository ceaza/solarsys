'''
QPIGS - General enquiry
QPIRI - Current settings enquiry
QMOD - Mode enquiry Line, Battery

Output Source Priority
POP00 - Set source to Utility first
POP01 - Set to solar first
POP02 - Set to solar Solar, Battary, Utility

Charger Source Priority
PCP00 - Utility first
PCP01 - Solar first
PCP02 - Utility and Solar
PCP03 - Solar only

'''



from pathlib import Path
from narada import Battery
from axpert import Axpert
from mppsolar import get_device_class
import logging
import configparser
import time
import os, sys
import crcmod
import json
import random

from multiprocessing import Process, Queue , Manager, Pool, Value , current_process

apikey = "5501428544958e9fc4827004e36922e4"
server = 'centurionsolar.co.za'
emoncmspath ='emoncms11'

config = configparser.ConfigParser()
logconfig = configparser.ConfigParser()
config['EMONCMS'] = {'apikey': '5501428544958e9fc4827004e36922e4',
                      'server': 'centurionsolar.co.za',
                      'emoncmspath': 'emoncms11'}
config['AXPERT'] = {'device': '/dev/hidraw0'
                        }
config['NARADA'] = {'device': '/dev/ttyUSB0'
                        }

print(os.getcwd())
user='pi'
config_file_name = Path(f'/home/{user}/github/solarsys').joinpath('conf.conf')
with open(config_file_name, 'w') as configfile:
    config.write(configfile)
config.read(config_file_name)
# create logger
logger = logging.getLogger(__name__)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('App has started')


class Battery1:
    def __init__(self):
        self.max_val = 10
        self.min_val = 0
        self.state = -1
        self.val = 10
    def get_values(self,new_state=None):
        print('State is',new_state)
        if int(new_state) in [1,-1]:
            self.state=int(new_state)
        if self.state ==-1:
            self.val = self.val + int(self.state)
            if self.val<=self.min_val:
                self.state = 1
        elif self.state ==1 :
            self.val = self.val + int(self.state)
            if self.val>=self.max_val:
                self.state=-1


class Inverter:
    def __init__(self):
        pass
    def get_values(self):
        return random.randint(1, 10)


c = Value('f',-1.0)

bsoc = Value('f', 0.0)

asoc = Value('f',0.0)
def inverter_service(bsoc,c,asoc):
    device_class = get_device_class('mppsolar')
    dev = device_class(port='/dev/hidraw0',protocol='PI30')
    inverter = Inverter()
    axpert = Axpert()
    try:
        name = current_process().name
        while True:
            res = axpert.run(command='QPIGS')
            print('charging_on:',res['device_status']['charging_on'])
            print(res)
            bsoc.acquire(),c.acquire(),asoc.acquire()
            if asoc.value <= 75.0 and asoc.value!=0:
                print('############## Must Stop Discharging Battery ###########')
                if res['device_status']['charging_on']==0: #scc_changing_on
                    dev.run_command('POP01')
                    print('POP01 command issued')
                
            if asoc.value >= 77.5:
                print('########### Can Discharge Now ###########')
                if res['device_status']['charging_on']==1:
                    print('POP02 command issued')
                    print(dev.run_command('POP02'))
            #print('Inverter Values=',inverter.get_values())
            print ("Inverter knows Average SOC = ",asoc.value)
            print ("Inverter knows Bat SOC = ",bsoc.value)
            bsoc.release(), c.release(),asoc.release()
            # time.sleep(1)
    except Exception as e:
        print(e)
        bsoc.release(),c.release(),asoc.release()

def battery_service(bat_soc,cz,ave_soc):
    bat = Battery()
    name = current_process().name
    # print (name,"Starting")
    time.sleep(1.0)
    # print (name, "Exiting")
    bat_dict = {}
    while True:
        try:
            for batid in [0,1,2,4]:
                bat_dic=bat.sendreceive(batid)
                if len(bat_dic)>0:
                    # print(f'Battery SOC:{bat_dic["soc"]}')
                    bat.send_all_data(bat_dic)
                    bat_soc.acquire(),cz.acquire(),ave_soc.acquire()
                    bat_soc.value = bat_dic['soc']
                    bat_dict[batid] = bat_dic['soc']
                    ave_soc.value = sum(bat_dict.values())/float(len(bat_dict))
                    print(bat_dict)
                    # print ("Battery Service SOC is =",az.value)
                    bat_soc.release(),cz.release(),ave_soc.release()
            #time.sleep(1)
        except Exception as e:
            print(e)
            bat_soc.release(),cz.release(),ave_soc.release()

if __name__ == '__main__':
    #Process(target=worker).start()
    # bat = Battery()
    # for x in range(1,100):
    #     bat.get_values()
    #     print(bat.val)

    run_battery = Process(name='battery', target=battery_service,args=(asoc,c,bsoc,))
    run_inverter = Process(name='Inverter', target=inverter_service,args=(asoc,c,bsoc,))
    #worker_2 = Process(target=worker,args=(a,)) # use default name

    run_battery.start()
    #worker_2.start()
    run_inverter.start()