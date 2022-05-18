// Click filter
 
// Filter elements
clas :: IPClassifier(10.0.0.0/24 and syn, -);
clone :: Tee();
clientInput :: FromDevice(filter-eth0);
backendInput :: FromDevice(filter-eth1);
// backupInput :: FromDevice(filter-eth2);
returnOut :: Queue(1024000) -> ToDevice(filter-eth0, BURST 51200);
mainOut :: Queue(1024000) -> ToDevice(filter-eth1, BURST 51200);
backupOut :: Queue(1024000) -> ToDevice(filter-eth2, BURST 51200);

// ARP res to 0, rest to 1
eth_classifier1 :: Classifier( 12/0806 20/0001,
                               - );
// ARP response
eth_classifier2 :: Classifier(12/0806 20/0002,
                              - );

// Client to backend - Separate ARP responses from other traffic
clientInput -> eth_classifier2;
eth_classifier2[0] -> mainOut;
eth_classifier2[1] -> Strip(14) -> CheckIPHeader() -> clone;
clone[0] -> Unstrip(14) -> mainOut;    
clone[1] -> clas;
clas[0] -> Unstrip(14) -> backupOut;
clas[1] -> Discard;

// Backend to client - Separate ARP requests
backendInput -> [0]eth_classifier1;
eth_classifier1[0] -> returnOut;           // ARP requests from NAT to client
eth_classifier1[1] -> returnOut;           // All other traffic
 
 
//                             normal traffic
// -------      ------      -------      -------
// |inport| -> |Cloner| -> |Outport| -> |backend|
// -------      ------      -------      -------
//                 |           
//                 |           SYN traffic
//                 |        ----------      --------
//                 ------> |Classifier| -> |outport2|
//                          ----------      --------

// Split traffic into two copies, drop all but SYN on copy

// TODO
//   Handle UDP streams

// Classify ARP req to 0, res to 1, rest to 2
// eth_classifier1 :: Classifier( 12/0806 20/0001,
//                                12/0806 20/0002,
//                                - );