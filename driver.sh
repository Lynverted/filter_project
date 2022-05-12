#!/bin/sh

#export PYTHONPATH=$PYTHONPATH:.

trap "sudo mn -c && sudo rm /var/run/click" EXIT
sudo python test-topology.py
sleep 1s
sudo rm /var/run/click
sudo rm /var/run/click2
sudo rm /var/run/click3