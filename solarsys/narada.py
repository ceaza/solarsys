import serial
import time
import io
from time import sleep
import json
import http.client as httplib


class Battery:
    apikey = "5501428544958e9fc4827004e36922e4"
    emons_server = 'centurionsolar.co.za'
    emoncmspath ='emoncms11'
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

    def __init__(self):
        try:
            ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1.5)
        except:
            ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1.5)

    def run(self):
        '''
        Run the batter service
        '''

        print(self.ser.name)
        print(self.ser)
        bat_list = self.get_bat_list()
        text = "b''"
        res = ''
        counter = 0
        bat_id = 0

        while True:
            for bat_id in bat_list:
                try:
                    print('Bat: {}'.format(bat_id))
                    self.ser.write(self.command(bat_id,1))
                    sleep(2)
                    #res =ser.readline()
                    res = self.ser.read_until('\n')
                    text = repr(res)
                    bat_id += 1
                except serial.SerialException as e:
                    print(e)

                if text!="b''":
                    print()
                    #bat_id += 1
                    #bat_id = 4 if bat_id == 3 else bat_id
                    counter += 1
                    buff = list(res)
                    # print(buff)
                    lst = buff
                    print(len(lst))
                    if len(lst)==90:
                        print(time.ctime(time.time()))
                        emons_dict = self.get_values(lst[:])
                        print(emons_dict)
                        self.send_all_data(emons_dict)
                    if len(lst)==92:
                        print(time.ctime(time.time()))
                        emons_dict = self.get_values(lst[:])
                        print(emons_dict)
                        self.send_all_data(emons_dict)
                    if len(lst)==922:
                        print(time.ctime(time.time()))	
                        emons_dict = self.get_values(lst[5:])
                        self.send_all_data(emons_dict)


    def send_data(self,data):
        try:
            conn = httplib.HTTPConnection(self.emons_server,timeout=5)
            string = "/"+self.emoncmspath+"/input/post.json?&node="+"Raspberry"+"&json="+data+"&apikey="+self.apikey
            print(string)
            conn.request("GET",string)
            response = conn.getresponse()
            print(response)
            conn.close()
        except:
            print('Cannot connect')
        
    def send_all_data(self,ddict):
        keys_to_send = ['soc','current','volts','temp']
        BATID = ddict['addr']
        sdict = {} 
        for k,v in ddict.items():
            if k in keys_to_send:
                if k=='temp':
                    sdict['Pylontech_Temperature'] = v[0]
                else:
                    sdict['{}_{}'.format(k,BATID)] = v
        data = json.dumps(sdict)
        data = data.replace('"','')
        data = data.replace(' ','')
        print(data)
        self.send_data(data)          

    def check(self,buf):
        ''' Create checksum '''
        chk = 0
        summ = 0
        for i in range(0,len(buf)):
            chk ^= buf[i]
            summ += buf[i]
        return (chk ^ summ) & 255


    def command(self,bat_id,command):
        '''Concat command with checksum '''
        wbuf = [126,bat_id,command,0]
        crc = self.check(wbuf)
        wbuf = wbuf+[crc,13]
        return bytes(wbuf)


    def cell_volts(self,cell_buff):
        '''work out volt per cell'''
        tv=0.0
        ltv=[]
        for cell in range(0,29,2):
            volts=(cell_buff[cell:cell+2])
            data0=format(volts[0],'#010b')[2:][3:]
            v=(int(data0,2)*256+volts[1])/1000.0
            ltv.append(v)
            tv+=v
        return tv,ltv

    def ftemp(self,cell_buff):
        '''work out temperature'''
        lt=[]
        for cell in range(0,9,2):
            its=(cell_buff[cell:cell+2])
            data0=its[0]
            t=((data0*256+its[1])-50.0)
            lt.append(t)
        return lt[:4]

    def fstatus(self,cell_buff):
        '''look up status'''
        lt=[]
        for cell in range(0,4,1):
            slist = format(cell_buff[cell],'#010b')[2:]
    #        print(slist)
            slist = [bool(int(b)) for b in slist]
            flags = [(self.status[cell][7-i],slist[i]) for i in range(7,-1,-1) if slist[i] ]
    #        print(flags)
            lt.append(flags)
        return lt

    def get_mapping(self,data_length):
        if data_length == 84:
            increment = -2
        elif data_length == 86:
            increment = 0
        mapping = {'head':[0,1,0,'ID'],
                'addr':[1,1,0,'BID'],
                'CID':[2,1,0,'ID'],
                'data_length':[3,1,0,'count'],
                'sub_volts':[4,1,0,'ID'],
                'number_cells':[5,1,0,'count'],
                'cell_volts':[6,30,lambda cv:self.cell_volts(cv),'volts'],
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
                'temp':[50,12+increment,lambda temp:self.ftemp(temp),'C'],
                'sub_status':[62+increment,1,0,'ID'],
                'number_status':[63+increment,1,0,'count'],        
                'status':[64+increment,10,lambda status:self.fstatus(status),'flag'],
                'sub_cycles':[74+increment,1,0,'ID'],
                'number_cycles':[75+increment,1,0,'count'],        
                'cycles':[76+increment,2,lambda x:(x[0]*256 + x[1]),'cycles'],
                'sub_packvolts':[78+increment,1,0,'ID'],
                'number_packvolts':[79+increment,1,0,'count'],        
                'packvolts': [80+increment,2,lambda x:(x[0]*256 + x[1])/100.0,'volts'],  
                'sub_soh':[82+increment,1,0,'ID'],
                'number_soh':[83+increment,1,0,'count'],        
                'soh':[84+increment,2,lambda x:(x[0]*256 + x[1])/100.0,'%']
                }
        return mapping

    def get_bat_list(self):
        bat_list = []
        for i in range(0,10):
            print(i)
            self.ser.write(self.command(i,1))  # sending command
            sleep(1)
            res = self.ser.read_until('\n')
            lst = list(res)
            print(lst)
            if len(lst)>5:
                bat_list.append(lst[1])
        print(bat_list)
        return bat_list


    #def get_data(buf):
    def get_values(self,buf):
        n=0
        out = {}
        for k,v in self.get_mapping(buf[3]).items():
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

if __name__ == "__main__":
    print('start service')
    bat = Battery()
    bat.run()


