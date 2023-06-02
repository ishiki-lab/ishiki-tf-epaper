#!/bin/bash
sudo apt-get install libusb-1.0-0 libudev1 procps
wget --backups=1 https://download.tinkerforge.com/tools/brickd/linux/brickd_linux_latest_armhf.deb
sudo dpkg -i brickd_linux_latest_armhf.deb
