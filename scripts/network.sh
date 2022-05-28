#!/bin/bash

down=false

# Disable network
if [ "$1" == "down" ]
    then
        echo "Down"
        # sudo ovs-ofctl mod-port bs1 1 down
        # sudo ovs-ofctl mod-port cs1 1 down
        sudo ip link set bs1-eth1 down
        sudo ip link set cs1-eth1 down

        #sudo ip link set switch1-eth1 down
        # for i in {1..5}
        # do 
        #     sudo ip link set servsw$i-eth1 down
        # done
fi

# enable network
if [ "$1" == "up" ]
    then
        echo "Up"
        sudo ovs-ofctl mod-port bs1 1 up
        sudo ovs-ofctl mod-port cs1 1 up
        sudo ip link set bs1-eth1 up
        sudo ip link set cs1-eth1 up
        
        #sudo ip link set switch1-eth1 up
        # for i in {1..5}
        # do 
        #     sudo ip link set servsw$i-eth1 up
        # done
fi

# Automated timer
if [ "$1" == "time" ]
    then
        counter=0
        while true; do
            # Wait 60 seconds before first failover
            if [ "$counter" -eq "0" ] ; then
                sleep 30
            fi

            # After 9 triggered failovers, exit
            if [ "$counter" -ge "18" ] ; then
                exit
            fi

            # Bring down interface
            if [ "$down" == "false" ] ; then
                echo "Down"
                sudo ovs-ofctl mod-port serversw 1 down
                sudo ovs-ofctl mod-port clientsw 1 down
                sudo ip link set clientsw-eth1 down
                sudo ip link set serversw-eth1 down
                down=true
            else
            # Bring up interface
                echo "Up"
                sudo ovs-ofctl mod-port serversw 1 up
                sudo ovs-ofctl mod-port clientsw 1 up
                sudo ip link set clientsw-eth1 up
                sudo ip link set serversw-eth1 up
                down=false
            fi
            counter=$((counter+1))
            sleep 30
        done
fi
