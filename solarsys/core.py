
from pathlib import Path
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
config_file_name = Path('/home/pi/github/solarsys').joinpath('conf.conf')
with open(config_file_name, 'w') as configfile:
    config.write(configfile)
config.read(config_file_name)
# create logger
logger = logging.getLogger(__name__)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('App has started')


class Battery:
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


c = Value('f',-1)

a = Value('f', 10)

def worker(a,c):
    inverter = Inverter()
    try:
        name = current_process().name
        while True:
            a.acquire(),c.acquire()
            if a.value <= 2:
                print('############## Issue Charge Command to Inverter ###########')
                c.value = float(1)
            if a.value >= 12:
                print('########### Issue Discharge Command to Inverter ###########')
                c.value = float(-1)           
            print('Inverter Values=',inverter.get_values())
            print ("Inverter knows SOC=",a.value)
            a.release(), c.release()
            time.sleep(1)
    except Exception as e:
        print(e)
        a.release(),c.release()

def my_service(az,cz):
    bat = Battery()
    name = current_process().name
    # print (name,"Starting")
    time.sleep(1.0)
    # print (name, "Exiting")
    
    while True:
        try:
            az.acquire(),cz.acquire()
            bat.get_values(cz.value)
            az.value=bat.val
            print()
            print ("SOC is =",az.value)
            az.release(),cz.release()
            time.sleep(2)
        except Exception as e:
            print(e)
            az.release(),cz.release()

if __name__ == '__main__':
    #Process(target=worker).start()
    # bat = Battery()
    # for x in range(1,100):
    #     bat.get_values()
    #     print(bat.val)

    service = Process(name='battery', target=my_service,args=(a,c,))
    worker_1 = Process(name='Inverter', target=worker,args=(a,c,))
    #worker_2 = Process(target=worker,args=(a,)) # use default name

    worker_1.start()
    #worker_2.start()
    service.start()