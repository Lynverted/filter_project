#!/bin/bash

down=false

# Disable network
if [ "$1" == "down" ]
    then
        echo "Down"

        sudo ip link set ss1-eth3 up
        sudo ip link set ss2-eth3 up
        sudo ip link set ss1-eth2 down
        sudo ip link set ss2-eth2 down
fi

# enable network
if [ "$1" == "up" ]
    then
        echo "Up"
        sudo ip link set ss1-eth3 down
        sudo ip link set ss2-eth3 down
        sudo ip link set ss1-eth2 up
        sudo ip link set ss2-eth2 up
fi

# Automated timer
if [ "$1" == "time" ]
    then
        counter=0
        delay=30
        nFail=1
        sleep=30
        
        while true; do
            # Wait N seconds before first failover
            if [ "$counter" -eq "0" ] ; then
                sleep $delay
            fi

            # After N triggered failovers, exit
            if [ "$counter" -ge "$nFail" ] ; then
                exit
            fi

            # Bring down interface
            if [ "$down" == "false" ] ; then
                echo "Down"
                sudo ip link set ss1-eth3 up
                sudo ip link set ss2-eth3 up
                sudo ip link set ss1-eth2 down
                sudo ip link set ss2-eth2 down
                down=true
            else
            # Bring up interface
                echo "Up"
                sudo ip link set ss1-eth3 down
                sudo ip link set ss2-eth3 down
                sudo ip link set ss1-eth2 up
                sudo ip link set ss2-eth2 up
                down=false
            fi
            counter=$((counter+1))
            sleep $sleep
        done
fi