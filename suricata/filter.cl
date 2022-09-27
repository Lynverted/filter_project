// Click filter
 
// Filter elements
clone :: Tee();
vlan2 :: VLANEncap(0x5678);

aggIP :: AggregateIPFlows();
agg1, agg2, agg3, agg4, agg5 :: AggregateFirst();

clientIn :: FromDevice(filter-eth1);
backendIn :: FromDevice(filter-eth2);
clientOut :: Queue(1024000) -> ToDevice(filter-eth1, BURST 51200);
backendOut :: Queue(1024000) -> ToDevice(filter-eth2, BURST 51200);

s2Out :: Unstrip(14) -> VLANEncap(0x1234) -> backendOut;

// Split traffic between S1 and S2
clientIn -> clone;

// Client to backend - S1 pipeline
clone[0] -> vlan2 -> backendOut;

// Client to backend - S2 pipeline
// Filter 5 packets through agg first elements to S2, discard rest
clone[1] -> Strip(14) -> CheckIPHeader() -> aggIP;
aggIP[0] -> agg1;
aggIP[1] -> Discard;
agg1[0] -> s2Out;
agg1[1] -> agg2;
agg2[0] -> s2Out;
agg2[1] -> agg3;
agg3[0] -> s2Out;
agg3[1] -> agg4;
agg4[0] -> s2Out;
agg4[1] -> agg5;
agg5[0] -> s2Out;
agg5[1] -> Discard;

// Backend to client
backendIn -> clientOut;


// Notes
 
// Packets need to be tagged with intended destination on exit given filter placement
// PaintSwitch takes no arguments but outputs port numbers that match whatever paint number it gets 

// Main in - front end:
//     Packet comes in to filter from eth0
//     Packet is sent to tee element 
//     Tee output 0 sends to S1 pipeline
//     Tee output 1 sends to the S2 pipeline 

// S1 pipeline:
//     Send packet to main out

// S2 pipeline:
//     Send packet to aggregate IP Flows element 
//     send output to aggregate first element 
//     Output 0 of aggregate first element is sent to S1 pipeline 
//     Output 1 of aggregate first element is sent to next agfirst element 
//     Repeat steps 5 times
//     Output 1 of 5th aggregate first element is sent to Discard 

// Main in - back end:
//     send directly to return out

