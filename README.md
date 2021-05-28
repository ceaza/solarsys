# solarsys


Additionally I recommend putting the following in the /etc/udev/rules.d/15-voltronic.rules

ATTRS{idVendor}=="0665", ATTRS{idProduct}=="5161", SUBSYSTEMS=="usb", ACTION=="add", MODE="0666", SYMLINK+="hidVoltronic"

ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", MODE="0666", SYMLINK+="ttyNarada"
It will create two files in /dev
