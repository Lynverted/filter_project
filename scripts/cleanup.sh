#!/bin/sh

sudo mn -c
sudo rm /var/run/click
sudo rm /var/run/click2
sudo rm /var/run/click3
sudo pkill -f "lighttpd"

echo "Cleanup complete."