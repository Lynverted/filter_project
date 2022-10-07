#!/bin/bash

down=false

# Disable network
if [ "$1" == "down" ]
    then
        echo "Down"

        sudo ip link set ss2-eth3 up
        sudo ip link set ss1-eth2 down
        sudo ip link set ss2-eth2 down
fi

# enable network
if [ "$1" == "up" ]
    then
        echo "Up"
        sudo ip link set ss2-eth3 down
        sudo ip link set ss1-eth2 up
        sudo ip link set ss2-eth2 up
fi