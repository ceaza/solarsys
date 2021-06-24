import os
from datetime import datetime
import sqlite3
from collections import OrderedDict
from pathlib import Path

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

#cur.execute('DROP TABLE MAIN_INVERTER')


#cur.execute(stmt, list(my_dict.values()))




class DataBase:
    
    def __init__(self):
        dbpath = Path(os.path.abspath(__file__)).parent.parent.joinpath('database')
        dbpath.mkdir(parents=True, exist_ok=True)
        dbfile = dbpath.joinpath('solarsys.db')
        print(dbfile)
        self.con = sqlite3.connect(dbfile)

    def _create_btable(self,cur):
        
        sql_txt = ''' CREATE TABLE IF NOT EXISTS BATTERY
            (id integer primary key autoincrement,
            date INTEGER,
            addr int,
            cell_volts text ,
            current real,
            soc real,
            capacity real,
            temp text,
            cycles int,
            packvolts real,
            soh real,
            processed BOOLEAN DEFAULT 0)
            '''
        cur.execute(sql_txt) 
    
    def _create_main_itable(self,cur):
        
        sql_txt = ''' CREATE TABLE IF NOT EXISTS MAIN_INVERTER
            (id integer primary key autoincrement,
            date INTEGER,
            gridvoltage real,
            grid_frequency real,
            inverter_voltage real,
            inverter_frequency real,
            apparent_power real,
            loadwatts real,
            loadpercentage real,
            busvoltage real,
            batteryvolts real,
            bat_charge_current real,
            soc real,
            inverter_temp real,
            pv_input_current_battery real,
            pvVolts1 real,
            bat_discharge_current real,
            SBU_priority integer,
            config_changed integer,
            SSC_firmware_updated integer,
            load_on integer,
            bat_volt_steady integer,
            charging_on integer,
            scc_changing_on integer,
            ac_on inetger,
            pvwatts real,
            batteryamps real,
            batterywatts real,
            pvAmps1 real,
            gridwatts real,
            SolarWatts real,
            processed BOOLEAN DEFAULT 0)
            '''
        cur.execute(sql_txt)        
        
    def output_dic(self,input_dict):
        my_dict = OrderedDict()
        for k,v in input_dict.items():
            if type(v)==dict:
                for k1,v1 in v.items():
                    my_dict[k1] = v1
            else:
                my_dict[k] = v
        return my_dict
    
    def write_data(self,table,my_dict):
        cur = self.con.cursor()
        table_name = 'inverter'
        #print(my_dict.keys())
        fields = (str(['date']+list(my_dict.keys())).replace("'",'')[1:-1])
        values = (str([str(datetime.now())]+list(my_dict.values()))[1:-1])
        sql = 'INSERT INTO ' + table + ' (' + fields + ') VALUES (' + values + ')'
        #print(fields)
        #print(values)
        # print(sql)
        cur.execute(sql)
        self.con.commit()
             
    def put_data(self,ddict):
        if 'inverter' in ddict.keys():
            sdict = self.output_dic(ddict['inverter'])
            # print(sdict)
            self.write_data('MAIN_INVERTER',sdict)
        elif 'bat' in ddict.keys():
            # print(ddict)
            ddict = ddict['bat']
            sdict = OrderedDict()
            for k,v in ddict.items():
                if k=='cell_volts':
                    sdict[k] = ','.join(map(str,v[1]))
                elif k == 'temp':
                    sdict[k] = ','.join(map(str,v))
                elif k != 'status':
                    sdict[k] = v
            self.write_data('BATTERY',sdict)
        else:
            pass
            print('Nothing')
        
if __name__ == '__main__':
    if 0:
        db = DataBase()
        cur = db.con.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        print(cur.execute(sql).fetchall())
        
    if 0:
        import pandas as pd
        db = DataBase()
        cur = db.con.cursor()
        db._create_main_itable(cur)
        db._create_btable(cur)
        db.con.commit()        

    if 0:
        db = DataBase()
        cur = db.con.cursor()
        sql = "ALTER TABLE MAIN_INVERTER ADD processed BOOLEAN DEFAULT 0 "
        print(cur.execute(sql).fetchall())

    if 0:
        db = DataBase()
        cur = db.con.cursor()
        cur.execute('DROP TABLE MAIN_INVERTER')
        cur.execute('DROP TABLE BATTERY')
        db.con.commit()
        db.con.close()
        
    if 0:
        import pandas as pd
        db = DataBase()
        cur = db.con.cursor()
        db._create_main_itable(cur)
        db._create_btable(cur)
        db.con.commit()
        db.put_data({'inverter':test_idata})
        db.put_data({'bat':test_bdata})
        db.con.commit()
        inv = pd.read_sql('SELECT * FROM MAIN_INVERTER',db.con,parse_dates=['date'])
        bat = pd.read_sql('SELECT * FROM BATTERY',db.con,parse_dates=['date'])
        print(inv)
        print(bat)
    if 0:
        import pandas as pd
        db = DataBase()
        cur = db.con.cursor()
        db._create_main_itable(cur)
        db._create_btable(cur)
        db.con.commit()
        #cur.execute('DROP TABLE MAIN_INVERTER1')
        #cur.execute('DROP TABLE BATTERY1')
        #db.con.commit()
        #1/0
        sql = 'INSERT INTO MAIN_INVERTER1 SELECT * FROM MAIN_INVERTER'
        cur.execute(sql)
        sql = 'INSERT INTO BATTERY1 SELECT * FROM BATTERY'
        cur.execute(sql)
        db.con.commit()
        sql = 'ALTER TABLE BATTERY RENAME TO BATTERY_D'
        cur.execute(sql)
        sql = 'ALTER TABLE BATTERY1 RENAME TO BATTERY'
        cur.execute(sql)
        sql = 'ALTER TABLE MAIN_INVERTER RENAME TO MAIN_INVERTER_D'
        cur.execute(sql)
        sql = 'ALTER TABLE MAIN_INVERTER1 RENAME TO MAIN_INVERTER'
        cur.execute(sql)        
        #db.con.close()
        inv = pd.read_sql('SELECT * FROM MAIN_INVERTER',db.con,parse_dates=['date'])
        print(type(inv.date.values[-1]))
        
    if 1:
        import pandas as pd
        import numpy as np
        db = DataBase()    
        cur = db.con.cursor()
        import pandas as pd
        import matplotlib.pyplot as plt
        inv = pd.read_sql('SELECT * FROM MAIN_INVERTER',db.con,parse_dates=['date'])
        bat = pd.read_sql('SELECT * FROM BATTERY',db.con,parse_dates=['date'])
        bat = bat.set_index('date')
        inv['tdelta'] = (inv.date - inv.shift(1).date)/np.timedelta64(1,'h')
        inv = inv[['date','gridwatts','loadwatts','batterywatts',
                   'SolarWatts','pvwatts','tdelta']].set_index('date')
        inv['pv_wh'] = inv['pvwatts'] * inv.tdelta 
        inv['load_wh'] = inv['loadwatts'] * inv.tdelta
        inv['grid_wh'] = inv['gridwatts'] * inv.tdelta
        inv['bat_wh'] = inv['batterywatts'] * inv.tdelta
        print(inv[['pvwatts','loadwatts']])
        print(inv[['pv_wh','load_wh','grid_wh','bat_wh']].groupby(pd.Grouper(freq='H')).sum()/1000.0)
        print(inv[['pv_wh','load_wh','grid_wh','bat_wh']].groupby(pd.Grouper(freq='D')).sum()/1000.0)
        inv[['pvwatts','loadwatts']].plot()
        #print(bat[['addr','cell_volts']])
        bat[[f'c{c}'for c in range(0,15)]] = bat.cell_volts.str.split(',',expand=True)
        bat[[f'c{c}'for c in range(0,15)]] = bat[[f'c{c}'for c in range(0,15)]].applymap(lambda x: float(x.strip()))
        if 0:
            for add in bat.addr.unique():
                bat[bat.addr==add][[f'c{c}'for c in range(0,15)]].plot(title=f'Battery {add}')
                
        #cells = cells.applymap(lambda x: float(x.strip()))
        #cells.plot()
        plt.show()
        #print(results2)
        db.con.close()
            
            
