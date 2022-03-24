// Click filter
 
// Assuming same testbed layout as before
// AddressInfo(
//   client1   10.1.0.1 10.1.0.0/24    00:00:00:01:00:01,
//   client2   10.1.0.2 10.1.0.0/24    00:00:00:01:00:02,
//   client3   10.1.0.3 10.1.0.0/24    00:00:00:01:00:03,
//   client4   10.1.0.4 10.1.0.0/24    00:00:00:01:00:04,
//   client5   10.1.0.5 10.1.0.0/24    00:00:00:01:00:05,
//   frontend  10.1.0.20 10.1.0.0/24   00:00:00:01:00:ff,
//   backends  10.0.0.254 10.0.0.0/24  00:00:00:00:00:ff,
//   backend1  10.0.0.1 10.0.0.0/24    00:00:00:00:00:01,
//   backend2  10.0.0.2 10.0.0.0/24    00:00:00:00:00:02,
//   backend3  10.0.0.3 10.0.0.0/24    00:00:00:00:00:03,
//   backend4  10.0.0.4 10.0.0.0/24    00:00:00:00:00:04,
//   backend5  10.0.0.5 10.0.0.0/24    00:00:00:00:00:05
// );
 
// Define filter elements
clas :: IPClassifier(syn, -);
clone :: Tee();
input :: FromDevice(click-eth0);
mainOut :: Queue(1024000) -> ToDevice(click-eth1, BURST 51200);
backupOut :: Queue(1024000) -> ToDevice(click-eth2, BURST 51200);
 
// // Link filter outputs 0,1 to out port and cloner to outport
input -> Strip(14) -> CheckIPHeader() -> clas;
clas[0] -> Unstrip(14) -> clone;
clas[1] -> Unstrip(14) -> mainOut;
clone[0] -> mainOut;
clone[1] -> backupOut;

// TODO
//   Drop ARP packets?
//   Handle UDP streams
//   Establish potential queue for exit ports
 
 
//                             normal traffic
// -------      ----------      -------
// |inport| -> |Classifier| -> |Outport|
// -------      ----------      -------
//                 |              ^
//                 |              |
//                 |            ------      --------
//                 ----------> |cloner| -> |outport2|
//                              ------      --------
// Classifier can't clone      Copied SYN packets

