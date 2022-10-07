from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import Node
from mininet.log import setLogLevel, info
import os

CLIENT_COUNT = 10
BACKEND_COUNT = 1

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

# Topology
class clickTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        self.serverswRules = []
        self.clientswRules = []

        info("*** Adding Switches\n")
        cs1 = self.addSwitch("cs1", dpid="101")
        bs1 = self.addSwitch("bs1", dpid="202")
        ss1 = self.addSwitch("ss1", dpid="303")
        ss2 = self.addSwitch("ss2", dpid="404")

        info("*** Adding routers\n")
        r1 = self.addHost("r1", cls=LinuxRouter, ip="10.0.0.1/24")
        r2 = self.addHost("r2", cls=LinuxRouter, ip="10.0.2.1/24")
        self.addLink(cs1, r1, params2={"ip": "10.0.0.1/24"}, addr2="00:00:00:00:00:99")
        self.addLink(bs1, r2, params2={"ip": "10.0.2.1/24"})
        self.addLink(r2, ss2, params1={"ip": "10.0.1.4/24"}, addr1="00:00:00:00:01:90")

        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        clients = []
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+2)), defaultRoute='via 10.0.0.1'))
            self.addLink(clients[c], cs1, addr1="00:00:00:00:00:0"+str(c+2))

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.2.{}/24".format(str(b+2)), defaultRoute='via 10.0.2.1'))
            self.addLink(backends[b], bs1, addr1="00:00:00:00:02:0"+str(b+2))

        info("*** Adding Filter\n")
        filter = self.addHost("filter", dpid="505")
        self.addLink(r1, ss1, params1={"ip": "10.0.1.1/24"}, addr1="00:00:00:00:01:99")
        self.addLink(ss1, filter)
        # self.addLink(r1, filter, params1={"ip": "10.0.1.1/24"}, addr1="00:00:00:00:01:99")
        # self.addLink(filter, ss1)

        info("*** Adding suricata\n")
        suri = self.addHost("s1", ip="10.0.1.2/24", defaultRoute='via 10.0.1.1')
        self.addLink(filter, suri, addr2="00:00:00:00:01:02")
        self.addLink(suri, ss2, addr1="00:00:00:00:01:03", params1={"ip": "10.0.1.3/24"})
        # self.addLink(suri, ss1, addr1="00:00:00:00:01:02")

        # Copy addresses
        suri2 = self.addHost("s2", ip="10.0.1.2/24", defaultRoute='via 10.0.1.1')
        self.addLink(suri2, ss1, addr1="00:00:00:00:01:02")
        self.addLink(suri2, ss2, addr1="00:00:00:00:01:03", params1={"ip": "10.0.1.3/24"})
        self.addLink(filter, suri2)

# Main method
def run():
    topo = clickTopo()
    net = Mininet(switch=OVSSwitch, build=False, topo=topo, controller=DefaultController, autoStaticArp=True, waitConnected=True)
    info("*** Starting Network\n")
    net.build()
    net.start()

    info("*** Starting HTTP Servers\n")
    backends = []
    for b in range(0, BACKEND_COUNT):
        backends.append(net.get('b' + str(b+1)))
        backends[b].cmd("sudo lighttpd -f ../backends/b"+str(b+1) + ".conf")
    
    # Static forwarding for switches
    for i in range(0, CLIENT_COUNT):
        net.get("cs1").cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:00:0" + str(i+2) + ",actions=output:"  + str(i+2) + "'")
    for i in range(0, BACKEND_COUNT):
        net.get("cs1").cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:02:0" + str(i+2) + ",actions=output:1'")
        net.get("bs1").cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:02:0" + str(i+2) + ",actions=output:"  + str(i+2) + "'")
        net.get("filter").cmd("ovs-ofctl -OOpenFlow13 add-flow filter 'dl_dst=00:00:00:00:02:0" + str(i+2) + ",actions=output:"  + str(i+2) + "'")

    # FF and redirect rules for the switches
    ss1 = net.get("ss1")
    ss1.cmd("ovs-ofctl -OOpenFlow13 add-group ss1 'group_id=1,type=ff,bucket=watch_port:2,output:2,bucket=watch_port:3,output:3'")
    # ss1.cmd("sudo ovs-ofctl -OOpenFlow13 add-flow ss1 'vlan_vid=0x1234,actions=strip_vlan,output:3'")
    # ss1.cmd("sudo ovs-ofctl -OOpenFlow13 add-flow ss1 'vlan_vid=0x5678,actions=strip_vlan,output:2'")
    ss1.cmd("ovs-ofctl -OOpenFlow10 add-flow ss1 'dl_type=0x800,nw_dst=10.0.1.2,priority=2,actions=group:1'")
    # ss1.cmd("ovs-ofctl -OOpenFlow13 add-flow ss1 'dl_type=0x806,nw_dst=10.0.1.2,priority=2,actions=group:1'")
    ss1.cmd("ovs-ofctl -OOpenFlow10 add-flow ss1 'dl_dst=00:00:00:00:01:02,priority=1,actions=group:1'")

    ss2 = net.get("ss2")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-group ss2 'group_id=1,type=ff,bucket=watch_port:2,output:2,bucket=watch_port:3,output:3'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_type=0x800,nw_dst=10.0.1.3,priority=2,actions=group:1'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_dst=00:00:00:00:01:03,priority=1,actions=group:1'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_type=0x800,nw_dst=10.0.2.2,priority=1,actions=output:1'")

    net.get("filter").cmd("click -u /var/run/click -f filter.cl &")
    net.get("filter").cmd("sudo ethtool --offload filter-eth0 tso off")
    net.get("filter").cmd("sudo ethtool --offload filter-eth0 gso off")
    net.get("filter").cmd("sudo ethtool --offload filter-eth0 gro off")
    net.get("filter").cmd("sudo ethtool --offload filter-eth1 tso off")
    net.get("filter").cmd("sudo ethtool --offload filter-eth1 tso off")
    net.get("filter").cmd("sudo ethtool --offload filter-eth1 tso off")

    # Suricata forwarding
    s1 = net.get("s1")
    s1.cmd("suricata -c config/suricata.yaml --pcap &")
    # s1.cmd("suricata -c config/suricata.yaml --af-packet &")
    s1.cmd("ip route add 10.0.1.1 dev s1-eth0")
    s1.cmd("ip route add 10.0.1.4 dev s1-eth1")
    s1.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")
    s1.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    s1.cmd("arp -s 10.0.1.1 00:00:00:00:01:99")
    s1.cmd("arp -s 10.0.1.4 00:00:00:00:01:90")
    
    s2 = net.get("s2")
    s2.cmd("suricata -c config/suricata2.yaml --pcap &")
    # s2.cmd("suricata -c config/suricata2.yaml --af-packet &")
    s2.cmd("ip route add 10.0.1.1 dev s2-eth0")
    s2.cmd("ip route add 10.0.1.4 dev s2-eth1")
    s2.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")
    s2.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    s2.cmd("arp -s 10.0.1.1 00:00:00:00:01:99")
    s2.cmd("arp -s 10.0.1.4 00:00:00:00:01:90")

    # Router directions
    net.get("r1").cmd("ip route add 10.0.2.0/24 via 10.0.1.2")
    net.get("r1").cmd("arp -s 10.0.0.10 00:00:00:00:00:10")
    net.get("r1").cmd("arp -s 10.0.0.11 00:00:00:00:00:11")
    net.get("r2").cmd("ip route add 10.0.0.0/24 via 10.0.1.3")
    net.get("r2").cmd("arp -s 10.0.1.3 00:00:00:00:01:03")

    # Kill S2 ports at start to prevent dupe traffic
    net.get("ss2").cmd("sudo ip link set ss1-eth3 down")
    net.get("ss2").cmd("sudo ip link set ss2-eth3 down")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo pkill -f "lighttpd"')
    os.system('sudo pkill -f "suricata"')
    os.system('sudo rm /var/run/click')

if __name__ == '__main__':
    setLogLevel('info')
    run()



    # Generate body of 10 clients - mixed traffic

    # info("*** Running traffic pcap gathering\n")
    # net.get("r1").cmd("tcpdump -i r1-eth0 -s 0 -w traffic.pcap &")
    # clients = []
    # for c in range(0, 10):
    #     clients.append(net.get('c' + str(c+1)))
    # popens = {}
    # log = open("output/fuck.txt", 'a')
    # log.flush()
    # for x in range(CLIENT_COUNT):
    #     if x <= 5:
    #         popens[x] = clients[x].popen("wrk -t 1 -c 2 -d 600 http://10.0.2.2/ &", stdout=log, shell=True, close_fds=True)
    #     if x > 5:
    #         popens[x] = clients[x].popen("gst-launch-1.0 -vvv playbin uri='http://10.0.2.2/bunny.mpd' video-sink=fakevideosink", shell=True)
    # print("Running clients")
    # for x in range(CLIENT_COUNT):
    #      popens[x].communicate()









    #  sudo ./id2t -i ../test.pcap -a DDoS ip.src=10.0.0.6 mac.src=00:00:00:00:00:06 inject.at-timestamp=1664392481

# click -u /var/run/click -f lb-click/lb.click

    # s1.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    # s1.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    # s1.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


# gst-launch-1.0 -vvv playbin uri='http://10.0.0.20/bunny.mpd' video-sink=fakevideosink 2>&1 | tee >(ts '%Y-%m-%d %H:%M:%.S' > /home/lyn/filter/output/gst/" \
                # + folder + "/raw" + str(x) + ".log) &", shell=True