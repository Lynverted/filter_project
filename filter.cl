// Click filter
 
// Filter elements
clas :: IPClassifier(syn);
clone :: Tee();
clientInput :: FromDevice(click-eth0);
backendInput :: FromDevice(click-eth1);
backupInput :: FromDevice(click-eth2);
returnOut :: Queue(1024000) -> ToDevice(click-eth0, BURST 51200);
mainOut :: Queue(1024000) -> ToDevice(click-eth1, BURST 51200);
backupOut :: Queue(1024000) -> ToDevice(click-eth2, BURST 51200);
 
// Client to backend - Re-ordering approach
// clientInput -> Strip(14) -> CheckIPHeader() -> clas;
// clas[0] -> Unstrip(14) -> clone;
// clas[1] -> Unstrip(14) -> mainOut;
// clone[0] -> mainOut;
// clone[1] -> backupOut;

// Backend responses
backendInput -> returnOut;

// Client to backend -  Non-reordering
clientInput -> clone;
clone[0] -> Strip(14) -> CheckIPHeader() -> Unstrip(14) -> mainOut;    // normal traffic
clone[1] -> strip(14) -> clas;
clas[0] -> CheckIPHeader() -> Unstrip(14) -> backupOut;                // Separated SYN packets

// Backend responses
backendInput -> returnOut;

// TODO
//   Drop ARP packets?
//   Handle UDP streams
 
 
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

