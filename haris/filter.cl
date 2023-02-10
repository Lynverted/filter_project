// Click filter

// Filter elements
clas :: IPClassifier(10.0.0.0/24 and syn, -);
clone :: Tee();
clientInput :: FromDevice(filter-eth0);
backendInput :: FromDevice(filter-eth1);
returnOut :: Queue(1024000) -> ToDevice(filter-eth0, BURST 51200);
mainOut :: Queue(1024000) -> ToDevice(filter-eth1, BURST 51200);
backupOut :: Queue(1024000) -> ToDevice(filter-eth2, BURST 51200);

// Classify ARP req to 0, res to 1, rest to 2
eth_classifier1 :: Classifier( 12/0806 20/0001,
                               12/0806 20/0002,
                               - );

// Client to backend - Separate ARP responses from other traffic
clientInput -> eth_classifier1;
eth_classifier1[0] -> Discard;                                               // drop ARP requests
eth_classifier1[1] -> mainOut;                                               // forward ARP responses
eth_classifier1[2] -> Strip(14) -> CheckIPHeader() -> clas;                  // all non ARP traffic
clas[0] -> Unstrip(14) -> clone;                                             // syn packets
clas[1] -> MarkIPHeader(0) -> SetTCPChecksum -> Unstrip(14) -> mainOut;
clone[0] -> SetTCPChecksum -> backupOut;                                     // SYN to backup
clone[1] -> SetTCPChecksum -> mainOut;                                       // SYN to main

// Backend to client - Separate ARP requests
backendInput -> Strip(14) -> MarkIPHeader(0) -> SetTCPChecksum -> Unstrip(14) -> returnOut;

 
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

// ARP res to 0, rest to 1
// eth_classifier1 :: Classifier( 12/0806 20/0001,
//                                - );
// ARP response
// eth_classifier2 :: Classifier(12/0806 20/0002,
//                               - );