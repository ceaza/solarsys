import os
from datetime import datetime
import sqlite3
from collections import OrderedDict
from pathlib import Path
import logging
from mppsolar import get_outputs

logger = logging.getLogger(__name__)

def output_dic(input_dict):
    my_dict = OrderedDict()
    for k,v in input_dict.items():
        if type(v)==dict:
            for k1,v1 in v.items():
                my_dict[k1] = v1
        else:
            my_dict[k] = v
    return my_dict

test_idata = {'gridvoltage': 229.1,
             'grid_frequency': 49.8,
             'inverter_voltage': 229.1,
             'inverter_frequency': 49.8,
             'apparent_power': 1053.0,
             'loadwatts': 976.0,
             'loadpercentage': 21.0,
             'busvoltage': 371.0,
             'batteryvolts': 50.2,
             'bat_charge_current': 2.0,
             'soc': 60.0, 'inverter_temp': 39.0,
             'pv_input_current_battery': 2.0,
             'pvVolts1': 212.6,
             'bat_discharge_current': 0.0,
             'device_status': {'SBU_priority': 0,
                               'config_changed': 0,
                               'SSC_firmware_updated': 0,
                               'load_on': 1,
                               'bat_volt_steady': 0,
                               'charging_on': 0,
                               'scc_changing_on': 1,
                               'ac_on': 0},
             'pvwatts': 145.0,
             'batteryamps': 2.0,
             'batterywatts': 100.4,
             'pvAmps1': 2.0,
             'gridwatts': 931.4000000000001,
             'SolarWatts': 44.59999999999991}

test_bdata = {'addr': 4,
             'cell_volts': (50.053, [3.337, 3.336, 3.337, 3.338, 3.336, 3.338, 3.337, 3.338, 3.337, 3.336, 3.336, 3.336, 3.335, 3.336, 3.34]),
             'current': 0.0,
             'soc': 77.87,
             'capacity': 112.76,
             'temp': [21.0, 21.0, 21.0, 21.0],
             'status': {'Charge_MOS_Error': 0,
                        'Discharge_MOS_Error': 0,
                        'Voltage_Module_Error': 0,
                        'NTC_Line_Disconnected': 0,
                        'Current_Module_Error': 0,
                        'Charge_Source_Reversed': 0,
                        'Discharge_OT_Protect': 0,
                        'Discharge_UT_Protect': 0,
                        'Charging': 0,
                        'Discharging': 0,
                        'Short_Current_Protect': 0,
                        'Over_Current_Protect': 0,
                        'Over_Voltage_Protect': 0,
                        'Under_Voltage_Protect': 0,
                        'Charge_OT_Protect': 0,
                        'Charge_UT_Protect': 0},
             'cycles': 558,
             'packvolts': 50.05,
             'soh': 100.0}

results = output_dic(test_idata)
outputs = get_outputs('json_mqtt')


mqtt_broker ="192.168.0.15"
mqtt_port = 1883
username = 'emqx'
password = 'public'
mqtt_user = username
mqtt_pass = password
filter = None
excl_filter =None

data=results
mqtt_broker=mqtt_broker
mqtt_port=mqtt_port
mqtt_user=mqtt_user
mqtt_pass=mqtt_pass,
mqtt_topic='python/mqtt'
filter=filter
excl_filter=excl_filter
keep_case=True
_tag = 'test'

while True:
    for op in outputs:
        # maybe include the command and what the command is im the output
        # eg QDI run, Display Inverter Default Settings
        logger.debug(f"Using output filter: {filter}")
        op.output(
            data=results,
            tag=_tag,
            mqtt_broker=mqtt_broker,
            mqtt_port=mqtt_port,
            mqtt_user=mqtt_user,
            mqtt_pass=mqtt_pass,
            mqtt_topic=mqtt_topic,
            filter=filter,
            excl_filter=excl_filter,
            keep_case=keep_case,
        )


