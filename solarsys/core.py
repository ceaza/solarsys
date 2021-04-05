
from pathlib import Path
import logging
import logging.config
import configparser
import time
import os, sys
import crcmod
import json
import os


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
config['LOGGING'] = {'level': '/dev/ttyUSB0'
                        }                      


config_file_name = Path(__file__).parent.parent.joinpath('conf.conf')
logging_config_file_name = Path(__file__).parent.parent.joinpath('logging.conf')
with open(config_file_name, 'w') as configfile:
    config.write(configfile)

config.read(config_file_name)

logging.config.fileConfig(logging_config_file_name)

# create logger
logger = logging.getLogger('simpleExample')

logger.debug('debug message')
logger.info('info message')
logger.warning('warn message')
logger.error('error message')
logger.critical('critical message')

 