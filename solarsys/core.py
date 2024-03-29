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
import pprint
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
# import random

from multiprocessing import Process, Queue , Manager, Pool, Value , current_process
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client import start_http_server


print(os.getcwd())
# Remove all handlers associated with the root logger object.
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

manager = Manager()
user='pi'
log_file_name = Path(f'/home/{user}/github/solarsys').joinpath('solarsys.log')
logging.basicConfig(filename=log_file_name, filemode='w',
                    format='%(asctime)s:%(levelname)s:%(message)s', level=logging.ERROR,
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


class CustomCollector(object):
    def __init__(self,q):
        self.q = q
        

    def collect(self):
        #rdict = self.q.get()
        if 1:
            while True:
                rdict = self.q.get()
                #print(rdict)
                if self.q.qsize()>2:
                    pass
                else:
                    break
        #rdict = self.q.get()
        #print('###########################################3#',rdict,self.q.qsize())


        for key, subdict in rdict.items():
            if key == 'inverter':
                gi = GaugeMetricFamily(key, 'Axpert values', labels=['metric'])
                for k,v in subdict.items():
                    if k!='device_status':
                        gi.add_metric([k],v)
                    else:
                        gis = GaugeMetricFamily('inverter_status', 'Axpert status values', labels=['metric'])
                        for kk,vv in v.items():
                            gis.add_metric([kk],vv)
                        yield gis
                yield gi
    
            elif key[:3] == 'bat':
                gb = GaugeMetricFamily(f'{key}','Battery values', labels=['metric'])
                for k,v in subdict.items():
                    if k=='status':
                        gbs = GaugeMetricFamily(f'battery_status_{key}', 'Battery status values', labels=['metric'])
                        for kk,vv in v.items():
                            gbs.add_metric([kk],vv)
                    elif k =='cell_volts':
                        gb.add_metric(['sum_cell_volts'],v[0])
                        gbv = GaugeMetricFamily(f'batteryvolts_{key}', 'Cell Volatages', labels=['metric'])
                        for i, volts in enumerate(v[1]):
                            gbv.add_metric([f'cell_{i:02d}'],volts)
                            #print([f'cell_{i}'],volts)
                    elif k =='temp':
                        gbt = GaugeMetricFamily(f'batterytemp_{key}', 'Cell Temperature', labels=['metric'])
                        for i, temp in enumerate(v):
                            gbt.add_metric([f'temp_{i:02d}'],temp)                            
                    else:
                        gb.add_metric([k],v)
                yield gb
                yield gbs
                yield gbv
                yield gbt

            
def prometheus_service(q):
    start_http_server(8000)
    #qdict = q.get()
    REGISTRY.register(CustomCollector(q))
    while True:
        pass



def send_emoncms(q):
    emoncms = Emoncms()
    while True:
        get_dict = q.get()
        #print(get_dict)
        if q.qsize()>100:
            pass
        else:
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
        


def inverter_service(bsoc,asoc,c,db,p):
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
    # get startup status
    command_status={'status':'there is no status yet'}
    status  = {'response':'there is no status yet'}
    for tr in range(10):
        logger.debug(f'Get status try: {tr}')
        status  = axpert.run(command='QPIRI',non_block=False)
        logger.info('Inverter Status:{}'.format(pprint.pformat(status)))  
        if 'response' in status.keys():
            logger.info('Response Status:{}'.format(pprint.pformat(status)))  
        else:
            break
    logger.info('Inverter Status:{}'.format(pprint.pformat(status)))    
    try:
        name = current_process().name
        while True:
            res = axpert.run(command='QPIGS')
            logger.debug(f"Grid charging_on:{res['device_status']['charging_on']}")
            logger.debug(f"Solar charging on:{res['device_status']['scc_changing_on']}")
            logger.debug(f"Solar watts:{res['SolarWatts']}")
            logger.debug('Output %s',res)
            bsoc.acquire(),asoc.acquire()
            res['asoc'] = asoc.value
            try:
                get_dict = c.get_nowait()
                get_dict['inverter'] = res
                p.put(get_dict)
            except:
                #pass
                # get_dict = {'inverter':{'device_status':{'no_data':1}}}
                p.put({'inverter':res})
             

            db.put({'inverter':res})
            if asoc.value <= 45.0 and asoc.value!=0:
                # logger.debug('####### Must Stop Discharging Battery #######')
                # We can check on this basis because of the way charge source
                # priorty is set. This will have to change if charge source set
                # to solar only
                # So this condition hold with PCP set to PCP02, charger source
                # Utility and Solar
                if res['device_status']['charging_on'] == 0:
                   # res['device_status']['scc_changing_on']==0: 
                    # status = axpert.run(command='QPIRI')
                    logger.debug('Status %s' % status)
                    logger.debug(f'Command Status for POP is: {status["POP"]}')
                    if status['POP'] != 0:
                        logger.debug('POP00 command issued')
                        cres = dev.run_command('POP00')
                        if cres['POP'][0] == 'ACK':
                            status['POP']=0
                        logger.info(f'POP00 command status: {cres}')

                
            if asoc.value >=50.0:
                # logger.debug('########### Can Discharge Now ###########')
                if res['device_status']['charging_on'] \
                   + res['device_status']['scc_changing_on'] == 1:
                    logger.debug('POP02 command issued if not already')
                    # status = axpert.run(command='QPIRI')
                    logger.debug('Status %s' % status)
                    logger.debug(f'Command Status for POP is: {status["POP"]}')
                    if status['POP'] != 2: 
                        cres = dev.run_command('POP02')
                        #cres = {'raw_response': ['(ACK9 \r', ''], '_command': 'POP02', '_command_description': 'Set Device Output Source Priority', 'POP': ['ACK', '']}
                        if cres['POP'][0] == 'ACK':
                            status['POP']=2
                        logger.info(f'POP02 command status {cres}')
                        command_status['POP02']=cres
            #print('Inverter Values=',inverter.get_values())
            print ("Inverter knows Average SOC = ",asoc.value)
            print ("Inverter knows Bat SOC = ",bsoc.value)
            bsoc.release(),asoc.release()
            # time.sleep(1)
    except Exception as e:
        logger.error(e)
        try:
            bsoc.release(),asoc.release()
        except:
            pass

def battery_service(bat_soc,ave_soc,cz,db):
    
    bat = Battery()
    name = current_process().name
    # print (name,"Starting")
    # time.sleep(1.0)
    # print (name, "Exiting")
    bat_soc_dict = {}
    allbatdict = {}
    n = 0
    while True:
        try:
            for batid in [0,1,2,4]:
                bat_dic = bat.sendreceive(batid)
                allbatdict[f'bat{batid}'] = bat_dic
#                 for k,v in bat_dic.items():
#                     if k in bat_dic['soc']:#['status','cell_volts','temp']:
                #cz[1] = [bat_dic['soc']]
                if len(bat_dic)>0:
                    # print(f'Battery SOC:{bat_dic["soc"]}')
                    # bat.send_all_data(bat_dic)
                    bat_soc.acquire(),ave_soc.acquire()
                    
                    #cz.put({'bat':bat_dic})
                    db.put({'bat':bat_dic})
                    cz.put(allbatdict)
                    # cz.put({'testing battery',123})
                    bat_soc.value = bat_dic['soc']
                    bat_soc_dict[batid] = bat_dic['soc']
                    # make sure we have all batteries before getting average.
                    if len(bat_soc_dict) == 4:
                        # print(allbatdict)
                        ave_soc.value = sum(bat_soc_dict.values())/float(len(bat_soc_dict))
                    print(bat_soc_dict)
                    #print ("Battery Service SOC is =",az.value)
                    bat_soc.release(),ave_soc.release()
                    n += 1
            #time.sleep(1)
        except Exception as e:
            logger.error(e)
            bat_soc.release(),ave_soc.release()
            

if __name__ == '__main__':
    prom = Queue()
    d = Queue()
    dbq = Queue()
    run_database = Process(name = 'Database', target=db_service,args=(dbq,))
    #send_data = Process(name='send_data', target=send_emoncms,args=(d,))
    run_battery = Process(name='battery', target=battery_service,args=(asoc,bsoc,d,dbq,))
    run_inverter = Process(name='Inverter', target=inverter_service,args=(asoc,bsoc,d,dbq,prom,))
    run_prometheus = Process(name='Prometheus', target=prometheus_service,args=(prom,))
    # send_data.start()
    run_battery.start()
    run_inverter.start()
    run_database.start()
    run_prometheus.start()

    

    
    