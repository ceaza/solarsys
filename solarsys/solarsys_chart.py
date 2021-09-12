from gpiozero import CPUTemperature
from datetime import datetime
from time import sleep, strftime, time
from database import DataBase
import matplotlib.pyplot as plt
import sqlite3
cpu = CPUTemperature()

plt.ion()
x = []
y = []

db = DataBase()



import pandas as pd
import numpy as np
db = DataBase()    
cur = db.con.cursor()
cur.execute('PRAGMA journal_mode=WAL;')
start_date = datetime(2021,9,3,7,30)
print(str(start_date))
inv = pd.read_sql(f' SELECT * FROM MAIN_INVERTER WHERE date > "{start_date}"',
                  db.con,parse_dates=['date'])

print(inv.columns)
#exit()

bat = pd.read_sql(f'SELECT * FROM BATTERY WHERE date > "{start_date}"',
                  db.con,parse_dates=['date'])
bat = bat.set_index('date')
print(bat)

inv['tdelta'] = (inv.date - inv.shift(1).date)/np.timedelta64(1,'h')
inv = inv[['date','gridwatts','loadwatts','batterywatts',
           'SolarWatts','pvwatts','tdelta']].set_index('date')
inv['pv_wh'] = inv['pvwatts'] * inv.tdelta 
inv['load_wh'] = inv['loadwatts'] * inv.tdelta
inv['grid_wh'] = inv['gridwatts'] * inv.tdelta
inv['bat_wh'] = inv['batterywatts'] * inv.tdelta
print(inv[['pvwatts','loadwatts']].tail())
hour_data = inv[['pv_wh','load_wh','grid_wh','bat_wh']].groupby(pd.Grouper(freq='H')).sum()/1000.0
hour_data.plot.bar(title='Hourly Graph')
print(inv[['pv_wh','load_wh','grid_wh','bat_wh']].groupby(pd.Grouper(freq='D')).sum()/1000.0)
#plt.figure()
if 0:
    cols = ['pvwatts','loadwatts','gridwatts','batterywatts']
    ax=inv[cols].plot()
    print(bat.tail())
    bat[bat.addr==0].soc.plot(ax=ax, secondary_y=True)
    lines = ax.get_lines() + ax.right_ax.get_lines()
    ax.legend(lines,cols + ['SOC'])


cols = ['pvwatts','loadwatts','gridwatts','batterywatts']
ax=inv[cols].plot()
print(bat.tail())
bat[bat.addr==0].soc.plot(ax=ax, secondary_y=True)
lines = ax.get_lines() + ax.right_ax.get_lines()
ax.legend(lines,cols +['SOC'])

cols = ['loadwatts']
ax=inv[cols].plot()
        #print(bat[['addr','cell_volts']])
bat[[f'c{c}'for c in range(0,15)]] = bat.cell_volts.str.split(',',expand=True)
bat[[f'c{c}'for c in range(0,15)]] = bat[[f'c{c}'for c in range(0,15)]].applymap(lambda x: float(x.strip()))
if 0:
    for add in bat.addr.unique():
        fig, axs = plt.subplots(nrows=2, ncols=1)
        fig.subplots_adjust(hspace=.7)
        print('Batt Number',add)
        cycles = bat[bat.addr==add].iloc[-1].cycles
        Over_Voltage_Protect = bat[bat.addr==add].iloc[-1].Over_Voltage_Protect
        Over_Voltage_Protect = 'True' if Over_Voltage_Protect == 1 else 'False'
        #ax0 = bat[bat.addr==add][[f'c{c}'for c in range(0,15)]].range().plot(title=f'Battery {add}')
        cell_range = bat[bat.addr==add][[f'c{c}'for c in range(0,15)]].max(axis=1) - \
            bat[bat.addr==add][[f'c{c}'for c in range(0,15)]].min(axis=1)
        ax1 = cell_range.plot(ax=axs[1],title=f'Vol tage Range vs. SOC \n Cycles:{cycles}')
        ax1.set_ylabel('Cell voltage range')
        bat[bat.addr==add].soc.plot(ax=ax1,secondary_y=True)
        ax1.right_ax.set_ylabel('SOC')
        cellvals = bat[bat.addr==add][[f'c{c}'for c in range(0,15)]].iloc[-1]
        cellvals = cellvals.to_frame('v')
        cellvals.plot.bar(ax=axs[0],title=f'Battery {add} \n Latest Cell volts \n Voltage Protect:{Over_Voltage_Protect}')
        axs[0].set_ylim(3.0,3.8)
        axs[0].set_ylabel('Cell Volts')
        fig.savefig(f'/home/pi/github/solarsys/docs/bat{add}_cell_volts.png',bbox_inches ="tight")

#exit()
def read_from_db():
    c.execute('SELECT * FROM stuffToPlot')
    data = c.fetchall()
    print(data)
    for row in data:
        print(row)

def write_temp(temp):
    with open("/home/pi/cpu_temp.csv", "a") as log:
        log.write("{0},{1}\n".format(strftime("%Y-%m-%d %H:%M:%S"),str(temp)))

def graph(temp):
    y.append(temp)
    x.append(time())
    plt.clf()
    plt.scatter(x,y)
    plt.plot(x,y)
    plt.draw()

while False:
    temp = cpu.temperature
    write_temp(temp)
    graph(temp)
    plt.pause(1)