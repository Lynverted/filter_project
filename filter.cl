// Click filter
 
// Filter elements
clas :: IPClassifier(syn, -);
clone :: Tee();
clientInput :: FromDevice(click-eth0);
backendInput :: FromDevice(click-eth1);
// backupInput :: FromDevice(click-eth2);
returnOut :: Queue(1024000) -> ToDevice(click-eth0, BURST 51200);
mainOut :: Queue(1024000) -> ToDevice(click-eth1, BURST 51200);
// backupOut :: Queue(1024000) -> ToDevice(click-eth2, BURST 51200);
 
// Client to backend - initial filtering
clientInput -> Strip(14) -> CheckIPHeader() -> clas;
clas[0] -> Unstrip(14) -> clone;
clas[1] -> Unstrip(14) -> mainOut;
clone[0] -> mainOut;
// clone[1] -> backupOut;

// Backend responses
backendInput -> returnOut;

// TODO
//   Drop ARP packets?
//   Handle UDP streams
//   Establish potential queue for exit ports
 
 
//                             normal traffic
// -------      ----------      -------      -------
// |inport| -> |Classifier| -> |Outport|    |backend|
// -------      ----------      -------      -------
//                 |              ^
//                 |              |
//                 |            ------      --------
//                 ----------> |cloner| -> |outport2|
//                              ------      --------
// Classifier can't clone      Copied SYN packets

