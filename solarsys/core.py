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
from emoncms import Emoncms
from database import DataBase

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
                    format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO,
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


#d = manager.dict()
#d[1]=[]
bsoc = Value('f', 0.0)
asoc = Value('f',0.0)

def send_emoncms(q):
    emoncms = Emoncms()
    while True:
        get_dict = q.get()
        #print(get_dict)
        emoncms.put_data(get_dict)
        print('No itmes in queue:', q.qsize())
        
def db_service(dbq):
    db = DataBase()
    while True:
        get_dict = dbq.get()
        #print(get_dict)
        db.put_data(get_dict)
           
def calc_service():
    '''
    This function calculates key system statistics
    PV produced for day
    PV produced for hour
    PV Max
    '''
    pass
    while True:
        db = DataBase()
        


def inverter_service(bsoc,asoc,c,db):
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
            bsoc.acquire(),asoc.acquire()
            c.put({'inverter':res})
            db.put({'inverter':res})
            if asoc.value <= 71.0 and asoc.value!=0:
                # logger.debug('####### Must Stop Discharging Battery #######')
                # We can check on this basis because of the way charge source
                # priorty is set. This will have to change if charge source set
                # to solar only8
                # So this condition hold with PCP set to PCP02, charger source
                # Utility and Solar
                if res['device_status']['charging_on'] == 0:
                   # res['device_status']['scc_changing_on']==0: 
                    cres = 'ACK'
                    status = axpert.run(command='QPIRI')
                    logger.debug('Status %s',status)
                    if status['POP'] != 0:
                        logger.debug('POP00 command issued')
                        cres = dev.run_command('POP00')
                        logger.debug(f'POP00 command status {cres}')

                
            if asoc.value >= 75.0:
                # logger.debug('########### Can Discharge Now ###########')
                if res['device_status']['charging_on'] \
                   + res['device_status']['scc_changing_on'] == 1:
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
        print('inverter error:',e)
        bsoc.release(),asoc.release()

def battery_service(bat_soc,ave_soc,cz,db):
    bat = Battery()
    name = current_process().name
    # print (name,"Starting")
    time.sleep(1.0)
    # print (name, "Exiting")
    bat_soc_dict = {}
    n = 0
    while True:
        try:
            for batid in [0,1,2,4]:
                bat_dic=bat.sendreceive(batid)
#                 for k,v in bat_dic.items():
#                     if k in bat_dic['soc']:#['status','cell_volts','temp']:
                #cz[1] = [bat_dic['soc']]
                if len(bat_dic)>0:
                    # print(f'Battery SOC:{bat_dic["soc"]}')
                    # bat.send_all_data(bat_dic)
                    bat_soc.acquire(),ave_soc.acquire()
                    cz.put({'bat':bat_dic})
                    db.put({'bat':bat_dic})
                    # cz.put({'testing battery',123})
                    bat_soc.value = bat_dic['soc']
                    bat_soc_dict[batid] = bat_dic['soc']
                    ave_soc.value = sum(bat_soc_dict.values())/float(len(bat_soc_dict))
                    print(bat_soc_dict)
                    # print ("Battery Service SOC is =",az.value)
                    bat_soc.release(),ave_soc.release()
                    n += 1
            #time.sleep(1)
        except Exception as e:
            logger.error(e)
            bat_soc.release(),ave_soc.release()
            

if __name__ == '__main__':
    d = Queue()
    dbq = Queue()
    run_battery = Process(name='battery', target=battery_service,args=(asoc,bsoc,d,dbq,))
    run_inverter = Process(name='Inverter', target=inverter_service,args=(asoc,bsoc,d,dbq,))
    run_database = Process(name = 'Database', target=db_service,args=(dbq,))
    send_data = Process(name='send_data', target=send_emoncms,args=(d,))

    run_battery.start()
    run_inverter.start()
    run_database.start()
    send_data.start()