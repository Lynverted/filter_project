// Click filter
 
// Assuming same testbed layout as before
AddressInfo(
  client1   10.1.0.1 10.1.0.0/24    00:00:00:01:00:01,
  client2   10.1.0.2 10.1.0.0/24    00:00:00:01:00:02,
  client3   10.1.0.3 10.1.0.0/24    00:00:00:01:00:03,
  client4   10.1.0.4 10.1.0.0/24    00:00:00:01:00:04,
  client5   10.1.0.5 10.1.0.0/24    00:00:00:01:00:05,
  frontend  10.1.0.20 10.1.0.0/24   00:00:00:01:00:ff,
  backends  10.0.0.254 10.0.0.0/24  00:00:00:00:00:ff,
  backend1  10.0.0.1 10.0.0.0/24    00:00:00:00:00:01,
  backend2  10.0.0.2 10.0.0.0/24    00:00:00:00:00:02,
  backend3  10.0.0.3 10.0.0.0/24    00:00:00:00:00:03,
  backend4  10.0.0.4 10.0.0.0/24    00:00:00:00:00:04,
  backend5  10.0.0.5 10.0.0.0/24    00:00:00:00:00:05
);
 
// Define filter elements
clas :: IPClassifier(syn, -);
clone :: Tee():
input :: FromDevice(eth0);
output :: ToDevice(eth1);
output2 :: ToDevice(eth2);
 
// Link filter outputs 0,1 to out port and cloner to outport
input -> [0]clas;
clas[0] -> [0]clone;
clas[1] -> output;
clone[0] -> output;
clone[1] -> output2;
 
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

