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
respond :: ARPResponder(10.0.0.0/24 00:00:00:00:00:dd);

// Classify ARP req to 0, res to 1, rest to 2
eth_classifier :: Classifier( 12/0806 20/0001,
                              12/0806 20/0002,
                              -
);
 
// ARP queries for responses
backendInput -> [0]eth_classifier; // Server responses go to classifier
eth_classifier[0] -> respond;      // ARP requests go to ARP responder
respond[0] -> mainOut;             // known backend responses
respond[1] -> returnOut;           // Proxied ARP requests
eth_classifier[1] -> mainOut;      // ARP responses go to NAT

// All other traffic
eth_classifier[2] -> returnOut;

// Backend responses
// backendInput -> returnOut;

// Client to backend -  Non-reordering
clientInput -> Strip(14) -> CheckIPHeader() -> clone;
clone[0] -> Unstrip(14) -> mainOut;    // normal traffic
clone[1] -> clas;
clas[0] -> Unstrip(14) -> backupOut;   // Separated SYN packets
clas[1] -> Discard;

 
 
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
//   Drop ARP packets?
//   Handle UDP streams

// Client to backend - Re-ordering approach
// clientInput -> Strip(14) -> CheckIPHeader() -> clas;
// clas[0] -> Unstrip(14) -> clone;
// clas[1] -> Unstrip(14) -> mainOut;
// clone[0] -> mainOut;
// clone[1] -> backupOut;