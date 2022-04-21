// basic NAT

AddressInfo(
  client1   10.0.0.1 10.0.0.0/24	00:00:00:00:00:01,
  client2   10.0.0.2 10.0.0.0/24	00:00:00:00:00:02,
  frontend  10.0.0.20 10.0.0.0/24	00:00:00:00:00:ff,
  backends  10.0.1.254 10.0.1.0/24 	00:00:00:00:01:ff,
  backend1  10.0.1.1 10.0.1.0/24 	00:00:00:00:01:01,
  backend2  10.0.1.2 10.0.1.0/24 	00:00:00:00:01:02,
  backend3  10.0.1.3 10.0.1.0/24 	00:00:00:00:01:03,
  backend4  10.0.1.4 10.0.1.0/24 	00:00:00:00:01:04,
  backend5  10.0.1.5 10.0.1.0/24 	00:00:00:00:01:05,
  backendSwitch 00:00:00:00:01:ee,
  clientSwitch 00:00:00:00:00:ee
);

// Classify ARP req to 0, res to 1, IP to 2, rest to 3
eth_classifier0, eth_classifier1 :: Classifier( 12/0806 20/0001,
                                                12/0806 20/0002,
                                                12/0800,
                                                -
);

backend_query :: ARPQuerier(frontend)
frontend_query :: ARPQuerier(frontend)

// Consistent backend mapper via source IP
backend_map :: SourceIPHashMapper(5 0xbadbeef,
                                 backends - backend1 - 0 1 4055,
                                 backends - backend2 - 0 1 80147,
                                 backends - backend3 - 0 1 37181,
                                 backends - backend4 - 0 1 36356,
                                 backends - backend5 - 0 1 3719
);

rewriter :: IPRewriter(backend_map,
                       drop,
                       TCP_TIMEOUT 30,
                       TCP_DONE_TIMEOUT 30,
                       TCP_NODATA_TIMEOUT 30
);

// Interfaces
from_clients :: FromDevice(click-eth0);
from_backends :: FromDevice(click-eth1);
to_clients :: Queue(1024000) -> ToDevice(click-eth0, BURST 51200);
to_backends :: Queue(1024000) -> ToDevice(click-eth1, BURST 51200);

// Packets go to classifier
from_clients -> [0]eth_classifier0;
from_backends -> [0]eth_classifier1;

// ARP requests
eth_classifier0[0] -> Discard;
eth_classifier1[0] -> Discard;
// ARP responses to querier
eth_classifier0[1] -> [1]frontend_query; // client
eth_classifier1[1] -> [1]backend_query; // backend

eth_classifier0[2] -> Strip(14) -> CheckIPHeader() -> [0]rewriter; // Clients
eth_classifier1[2] -> Strip(14) -> CheckIPHeader() -> [1]rewriter; // Backends

eth_classifier0[3] -> Discard;
eth_classifier1[3] -> Discard;

rewriter[0] -> SetTCPChecksum() -> [0]backend_query[0] -> to_backends;
rewriter[1] -> SetTCPChecksum() -> [0]frontend_query[0] ->  to_clients;
// rewriter[0] -> SetTCPChecksum() -> EtherEncap(0x800, backends, backend1) -> to_backends;
