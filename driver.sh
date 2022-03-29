#!/bin/sh

#export PYTHONPATH=$PYTHONPATH:.

trap "sudo mn -c && sudo rm /var/run/click" EXIT
sudo python test-topology.py