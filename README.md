# filter_project
Traffic filter state recreation experiment


To use the suricata branch testing:
1. Run the topology (sudo python topo.py)
2. Once it has started and both instances of suricata are running, run the following command: r1 tcpreplay-edit -i r1-eth1 --enet-dmac 00:00:00:00:01:02 -C --mtu-trunc --mbps 1000 pcaps/2017-X.pcap"
    2a. Change the chosen pcap day to monday to thursday, depending on the chosen CICID2017 dataset you're testing
3. When the stream is complete, tear down the mininet with "exit"
4. Run the total jq map for overall numbered results (./jq-sum.sh)
5. Run the jq maps individually for specific alerts (jq -s -f map.jq log/suriX/eve.json) changing the suri number to 1 or 2 for the primary or redundant respectively
6. Delete both sets of logs to ensure clean results when finished (sudio rm log/suriX/*)
7. Run the failure command to initiate network failures (./network.sh X) with up or down respectively
