#help('mppsolar.devices')
 


from mppsolar import get_device_class


device_class = get_device_class('mppsolar')

# help(device_class)
dev = device_class(port='/dev/hidraw0',protocol='PI30')
# print(dev.list_commands().keys())
print(dev.run_command('POP02'))

while False:
    print()
    res = dev.run_command('QPIGS')
    for k,v in res.items():
        print(k,v)
#print(dev.run_command('POP02'))
