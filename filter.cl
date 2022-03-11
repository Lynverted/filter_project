// Click filter

// Packet cloner element - takes SYN, copies and returns both output
elementclass packetCloner {

}


clas :: IPClassifier(syn, -);
clone :: packetCloner() // Not made yet



FromDevice(eth0) -> clas;
clas[0] -> 