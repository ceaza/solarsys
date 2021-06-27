from mppsolar import get_device_class
device_class = get_device_class('mppsolar')
dev = device_class(port='/dev/hidraw0',protocol='PI30')
cres = dev.run_command('POP00')

print(cres)
print(cres['POP'][0] == 'ACK')


cres = dev.run_command('QPIGS')

print(cres)