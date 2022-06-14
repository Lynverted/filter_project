#!/bin/bash

down=false

# Disable network
if [ "$1" == "down" ]
    then
        echo "Down"

        sudo ip link set bs1-eth1 down
        sudo ip link set cs1-eth1 down
fi

# enable network
if [ "$1" == "up" ]
    then
        echo "Up"

        sudo ip link set bs1-eth1 up
        sudo ip link set cs1-eth1 up
fi

# Automated timer
if [ "$1" == "time" ]
    then
        counter=0
        delay=0
        nFail=0
        sleep=0

        if [ "$2" == "wrk" ]
        then 
            delay=10
            nFail=12
            sleep=10
        fi
        
        if [ "$2" == "gst" ]
        then 
            delay=30
            nFail=20
            sleep=50
        fi
        
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
                sudo ip link set bs1-eth1 down
                sudo ip link set cs1-eth1 down
                down=true
            else
            # Bring up interface
                echo "Up"
                sudo ip link set bs1-eth1 up
                sudo ip link set cs1-eth1 up
                down=false
            fi
            counter=$((counter+1))
            sleep $sleep
        done
fi
