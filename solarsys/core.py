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

import logging
from pathlib import Path
from narada import Battery
from axpert import Axpert
from mppsolar import get_device_class

import configparser
import time
import os, sys
import crcmod
import json
import random

from multiprocessing import Process, Queue , Manager, Pool, Value , current_process
print(os.getcwd())
# Remove all handlers associated with the root logger object.
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

manager = Manager()
user='pi'
log_file_name = Path(f'/home/{user}/github/solarsys').joinpath('solarsys.log')
logging.basicConfig(filename=log_file_name, filemode='w',
                    format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG,
                    datefmt = '%Y-%m-%d %H:%M:%S')

stdout_handler = logging.StreamHandler(sys.stdout)

                    
apikey = "5501428544958e9fc4827004e36922e4"
server = 'centurionsolar.co.za'
emoncmspath ='emoncms11'

config = configparser.ConfigParser()

config['EMONCMS'] = {'apikey': '5501428544958e9fc4827004e36922e4',
                      'server': 'centurionsolar.co.za',
                      'emoncmspath': 'emoncms11'}
config['AXPERT'] = {'device': '/dev/hidraw0'
                        }
config['NARADA'] = {'device': '/dev/ttyUSB0'
                        }


config_file_name = Path(f'/home/{user}/github/solarsys').joinpath('conf.conf')

with open(config_file_name, 'w') as configfile:
    config.write(configfile)
config.read(config_file_name)
# create logger

logger = logging.getLogger(__name__)
logger.addHandler(stdout_handler)
logger.debug('App has started')


d = manager.dict()
bsoc = Value('f', 0.0)
asoc = Value('f',0.0)


def inverter_service(bsoc,asoc,c):
    '''
    This routine controls when the inverter switches between using the battery
    and not as a source for the output.
    The POP command controls the following modes:
    * POP00: Utility only    
    * POP01: Solar first mode
    * POP02: SBU or Solar, Battery then Utility
    
    Because of earth leak in panels we set charger source priority to Solar and utility
    but set utility charging to only 2 amp.

    asoc : average battery state of charge in percent
    '''
    device_class = get_device_class('mppsolar')
    dev = device_class(port='/dev/hidraw0',protocol='PI30')
    axpert = Axpert()
    try:
        name = current_process().name
        while True:
            res = axpert.run(command='QPIGS')
            logger.debug(f"Grid charging_on:{res['device_status']['charging_on']}")
            logger.debug(f"Solar charging on:{res['device_status']['scc_changing_on']}")
            logger.debug(f"Solar watts:{res['SolarWatts']}")
            logger.debug('Output %s',res)
            # print(c)
            bsoc.acquire(),asoc.acquire()
            if asoc.value <= 77.0 and asoc.value!=0:
                # logger.debug('####### Must Stop Discharging Battery #######')
                # We can check on this basis because of the way charge source
                # priorty is set. This will have to change if charge source set
                # to solar only
                # So this condition hold with PCP set to PCP02, charger source
                # Utility and Solar
                if res['device_status']['charging_on'] + \
                   res['device_status']['scc_changing_on']==0: 
                    logger.debug('POP01 command issued')
                    cres = 'ACK'
                    status = axpert.run(command='QPIRI')
                    logger.debug('Status %s',status)
                    if status['POP'] != 1:
                        cres = dev.run_command('POP01')
                        logger.debug(f'POP01 command status {cres}')

                
            if asoc.value >= 80.0:
                # logger.debug('########### Can Discharge Now ###########')
                if res['device_status']['charging_on']==1:
                    print('POP02 command issued')
                    logger.debug('POP02 command issued')
                    cres = 'ACK'
                    status = axpert.run(command='QPIRI')
                    logger.debug('Status %s',status)
                    if status['POP'] != 2:
                        cres = dev.run_command('POP02')
                        logger.debug(f'POP02 command status {cres}')
            #print('Inverter Values=',inverter.get_values())
            print ("Inverter knows Average SOC = ",asoc.value)
            print ("Inverter knows Bat SOC = ",bsoc.value)
            bsoc.release(),asoc.release()
            # time.sleep(1)
    except Exception as e:
        print(e)
        bsoc.release(),asoc.release()

def battery_service(bat_soc,ave_soc,cz):
    bat = Battery()
    name = current_process().name
    # print (name,"Starting")
    time.sleep(1.0)
    # print (name, "Exiting")
    bat_soc_dict = {}
    while True:
        try:
            for batid in [0,1,2,4]:
                bat_dic=bat.sendreceive(batid)
                cz = bat_dic
                if len(bat_dic)>0:
                    # print(f'Battery SOC:{bat_dic["soc"]}')
                    bat.send_all_data(bat_dic)
                    bat_soc.acquire(),ave_soc.acquire()
                    bat_soc.value = bat_dic['soc']
                    bat_soc_dict[batid] = bat_dic['soc']
                    ave_soc.value = sum(bat_soc_dict.values())/float(len(bat_soc_dict))
                    print(bat_soc_dict)
                    # print ("Battery Service SOC is =",az.value)
                    bat_soc.release(),ave_soc.release()
            #time.sleep(1)
        except Exception as e:
            print(e)
            bat_soc.release(),ave_soc.release()

if __name__ == '__main__':


    run_battery = Process(name='battery', target=battery_service,args=(asoc,bsoc,d,))
    run_inverter = Process(name='Inverter', target=inverter_service,args=(asoc,bsoc,d,))
    #worker_2 = Process(target=worker,args=(a,)) # use default name

    run_battery.start()
    #worker_2.start()
    run_inverter.start()