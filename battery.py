import serial
import time
import io
from time import sleep
import json


def check(buf):
    chk = 0
    summ = 0
    for i in range(0,len(buf)):
        chk ^= buf[i]
        summ += buf[i]
    return (chk ^ summ) & 255



apikey = "5501428544958e9fc4827004e36922e4"
server = 'centurionsolar.co.za'
emoncmspath ='emoncms11'




import http.client as httplib
def send_data(data):
    conn = httplib.HTTPConnection(server)
    string = "/"+emoncmspath+"/input/post.json?&node="+"Raspberry"+"&json="+data+"&apikey="+apikey
    print(string)
    conn.request("GET",string)
    response = conn.getresponse()
    print(response)
    conn.close()
    
def send_all_data(ddict):
    keys_to_send = ['soc','current','volts']
    BATID = ddict['addr']
    sdict = {} 
    for k,v in ddict.items():
        if k in keys_to_send:
            sdict['{}_{}'.format(k,BATID)] = v
    data = json.dumps(sdict)
    data = data.replace('"','')
    data = data.replace(' ','')
    print(data)
    send_data(data)
    
    
            

status = {0:{
    0: '(Reserved)',
    1: '(Reserved)',
    2: '(Reserved)',
    3: '(Reserved)',
    4: '(Reserved)',
    5: 'Charge_MOS_Error',
    6: 'Discharge_MOS_Error',
    7: 'Voltage_Module_Error'},
    1:{
    0: 'NTC_Line_Disconnected',
    1: 'Current_Module_Error',
    2: 'Charge_Source_Reversed',
    3: '(Reserved)',
    4: '(Reserved)',
    5: '(Reserved)',
    6:'(Reserved)',
    7: '(Reserved)'},
    2:{
    0: 'Discharge_OT_Protect',
    1: 'Discharge_UT_Protect',
    2: '(Reserved)',
    3: '(Reserved)',
    4: '(Reserved)',
    5: '(Reserved)',
    6: '(Reserved)',
    7: '(Reserved)'},

    3:{
    0: 'Charging',
    1: 'Discharging',
    2: 'Short_Current_Protect',
    3: 'Over_Current_Protect',
    4: 'Over_Voltage_Protect',
    5: 'Under_Voltage_Protect',
    6: 'Charge_OT_Protect',
    7: 'Charge_UT_Protect'}}


def cell_volts(cell_buff):
    tv=0.0
    ltv=[]
    for cell in range(0,29,2):
        volts=(cell_buff[cell:cell+2])
        data0=format(volts[0],'#010b')[2:][3:]
        v=(int(data0,2)*256+volts[1])/1000.0
        ltv.append(v)
        tv+=v
    return tv,ltv

def ftemp(cell_buff):

    lt=[]
    for cell in range(0,9,2):
        its=(cell_buff[cell:cell+2])
        data0=its[0]
        t=((data0*256+its[1])-50.0)
        lt.append(t)
    return lt[:4]

def fstatus(cell_buff):
    
    lt=[]
    for cell in range(0,4,1):
        slist = format(cell_buff[cell],'#010b')[2:]
#        print(slist)
        slist = [bool(int(b)) for b in slist]
        flags = [(status[cell][7-i],slist[i]) for i in range(7,-1,-1) if slist[i] ]
#        print(flags)
        lt.append(flags)
        
    return lt


mapping ={'head':[0,1,0,'ID'],
        'addr':[1,1,0,'BID'],
        'CID':[2,1,0,'ID'],
        'data_length':[3,1,0,'count'],
        'sub_volts':[4,1,0,'ID'],
        'number_cells':[5,1,0,'count'],
        'cell_volts':[6,30,lambda cv:cell_volts(cv),'volts'],
        'sub_current':[36,1,0,'ID'],
        'number_current':[37,1,0,'count'],
        'current':[38,2,lambda amps:(30000.0-(amps[0]*256 + amps[1]))/100.0,'amps'],
        'sub_soc':[40,1,0,'ID'],
        'number_soc':[41,1,0,'count'],
        'soc':[42,2,lambda soc:(soc[0]*256 + soc[1])/100.0,'%'],
        'sub_capacity':[44,1,0,'ID'],
        'number_capicity':[45,1,0,'count'],
        'capacity':[46,2,lambda cap:(cap[0]*256 + cap[1])/100.0,'ah'],
        'sub_temp':[48,1,0,'ID'],
        'number_temp':[49,1,0,'count'],        
        'temp':[50,12,lambda temp:ftemp(temp),'C'],
        'sub_status':[62,1,0,'ID'],
        'number_status':[63,1,0,'count'],        
        'status':[64,10,lambda status:fstatus(status),'flag'],
        'sub_cycles':[74,1,0,'ID'],
        'number_cycles':[75,1,0,'count'],        
        'cycles':[76,2,lambda x:(x[0]*256 + x[1]),'cycles'],
        'sub_packvolts':[78,1,0,'ID'],
        'number_packvolts':[79,1,0,'count'],        
        'packvolts': [80,2,lambda x:(x[0]*256 + x[1])/100.0,'volts'],  
        'sub_soh':[82,1,0,'ID'],
        'number_soh':[83,1,0,'count'],        
        'soh':[84,2,lambda x:(x[0]*256 + x[1])/100.0,'%']}


#def get_data(buf):
def get_values(buf):
    n=0
    out = {}
    for k,v in mapping.items():
        if v[3] not in ['ID','count']:
            f = (lambda x:x) if v[2] == 0 else v[2]
            val_in =buf[v[0]:v[0]+v[1]]
            val = f(val_in)
            print('{}::{} {}'.format(k,val,v[3]))
            if k== 'addr':
                val = val[0]
            out[k] = val
            n+=v[1]
    return out

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)





def command(bat_id,command):
    wbuf = [126,bat_id,command,0]
    crc = check(wbuf)
    wbuf = wbuf+[crc,13]
    return wbuf


print(ser.name)
print(ser)
text = "b''"
res = ''
lines = []
counter = 0
bat_id=0

while True:
    try:
        bat_id^=1
        write_val = command(bat_id,1)
        write_byte = bytes(write_val)
##        print('Bat: {}'.format(bat_id))
        ser.write(write_byte)
        sleep(10)
        res =ser.readline()
        text = repr(res)
        counter += 1
    except serial.SerialException as e:
        print(e)
    if text!="b''":
        buff = list(res)
        lst = buff
        if len(lst)==5:
            lst = lst+last_lst
        if len(lst)==92:
            emons_dict = get_values(lst[5:])
            send_all_data(emons_dict)
##            emons_json = json.dumps(emons_dict)
##            emons_json = emons_json.replace('"','')
##            send_data(emons_json)
            print()
        last_lst = lst 

    lines.append(list(res))
    if counter==10000:
        break
    
    
mylist =lines
with open('output5.csv', 'w',) as myfile:
    for l in mylist:
        sl = ','.join([str(i) for i in l]) + '\n'
        myfile.write(sl)
myfile.close()    
        
   
