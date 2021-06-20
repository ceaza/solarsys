import http.client as httplib
import json

class Emoncms:
    
    def __init__(self,timeout=5):
        self.timeout = timeout
        self.apikey = "5501428544958e9fc4827004e36922e4"
        self.emon_server = 'centurionsolar.co.za'
        self.emoncmspath ='emoncms11'
    
    def send_data(self,data):
        conn = httplib.HTTPConnection(self.emon_server,timeout=self.timeout)
        string = "/"+self.emoncmspath+"/input/post.json?&node=" \
                 +"Raspberry"+"&json="+data+"&apikey="+ self.apikey
        #print(string)
        conn.request("GET",string)
        response = conn.getresponse()
        print(response)
        conn.close()
        
    def send_bat_data(self,ddict):
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
        # print(data)
        self.send_data(data)        

    def send_inverter_data(self,ddict):
        keys_to_not_send = ['device_status','pvw atts','gri dvoltage']
        # keys_to_send = ['soc','current','volts','temp']
        sdict = {} 
        for k,v in ddict.items():
            if k not in keys_to_not_send:
                sdict['{}'.format(k)] = v
        data = json.dumps(sdict)
        data = data.replace('"','')
        data = data.replace(' ','')
        # print(data)
        try:
            self.send_data(data)
        except:
            print('timed out')
            
    def put_data(self,ddict):
        if 'bat' in ddict.keys():
            self.send_bat_data(ddict['bat'])
        elif 'inverter' in ddict.keys():
            self.send_inverter_data(ddict['inverter'])
        else:
            pass
    
            
            