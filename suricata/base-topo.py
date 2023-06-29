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
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        self.cmd( 'echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter')

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
        self.addLink(bs1, r2, params2={"ip": "10.0.2.1/24"}, addr2="00:00:00:00:02:90")
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

        info("*** Adding suricata\n")
        suri = self.addHost("s1", ip="10.0.1.2/24", defaultRoute='via 10.0.1.1')
        self.addLink(filter, suri, addr2="00:00:00:00:01:02")
        self.addLink(suri, ss2, addr1="00:00:00:00:01:03", params1={"ip": "10.0.1.3/24"})

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
        # backends[b].cmd("sudo lighttpd -f ../backends/b"+str(b+1) + ".conf")
    
    # Static forwarding for switches
    for i in range(0, CLIENT_COUNT):
        net.get("cs1").cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:00:0" + str(i+2) + ",actions=output:"  + str(i+2) + "'")
        net.get("bs1").cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:00:0" + str(i+2) + ",actions=output:1'")
    for i in range(0, BACKEND_COUNT):
        net.get("cs1").cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:02:0" + str(i+2) + ",actions=output:1'")
        net.get("bs1").cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:02:0" + str(i+2) + ",actions=output:"  + str(i+2) + "'")
    net.get("cs1").cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_type=0x800,nw_dst=10.0.2.2,actions=output:1'")
    net.get("bs1").cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:02:90,actions=output:1'")

    # FF and redirect rules for the switches
    ss1 = net.get("ss1")
    ss1.cmd("ovs-ofctl -OOpenFlow13 add-group ss1 'group_id=1,type=ff,bucket=watch_port:2,output:2,bucket=watch_port:3,output:3'")
    ss1.cmd("ovs-ofctl -OOpenFlow10 add-flow ss1 'dl_type=0x800,nw_dst=10.0.1.2,priority=2,actions=group:1'")
    ss1.cmd("ovs-ofctl -OOpenFlow10 add-flow ss1 'dl_dst=00:00:00:00:01:02,priority=1,actions=group:1'")
    ss1.cmd("ovs-ofctl -OOpenFlow13 add-flow ss1 'dl_dst=00:00:00:00:01:99,priority=1,actions=output:1'")

    ss2 = net.get("ss2")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-group ss2 'group_id=1,type=ff,bucket=watch_port:2,output:2,bucket=watch_port:3,output:3'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_type=0x800,nw_dst=10.0.1.3,priority=2,actions=group:1'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_dst=00:00:00:00:01:03,priority=1,actions=group:1'")
    ss2.cmd("ovs-ofctl -OOpenFlow13 add-flow ss2 'dl_dst=00:00:00:00:01:90,priority=1,actions=output:1'")

    # Filter 
    net.get("filter").cmd("click -u /var/run/click -f filter.cl &")
    # net.get("filter").cmd("click -u /var/run/click -f filter2.cl &")
    flag = ["tso", "gso", "gro"]
    for x in range(0, 6):
        if(x % 2): 
            net.get('filter').cmd("sudo ethtool --offload filter-eth" + str(x % 2) + " " + flag[x/2] + " off")
            net.get('filter').cmd("sudo ethtool --offload filter-eth" + str((x % 2)+1) + " " + flag[x/2] + " off")
        else:
            net.get('filter').cmd("sudo ethtool --offload filter-eth" + str(x % 2) + " " + flag[x/2] + " off")


    # Suricata forwarding
    s1 = net.get("s1")
    s1.cmd("sysctl net.ipv4.ip_forward=1")
    # s1.cmd("suricata -c config/suricata.yaml --pcap &")
    s1.cmd("ip route add 10.0.1.1 dev s1-eth0")
    s1.cmd("ip route add 10.0.1.4 dev s1-eth1")
    s1.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")
    s1.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    s1.cmd("arp -s 10.0.1.1 00:00:00:00:01:99")
    s1.cmd("arp -s 10.0.1.4 00:00:00:00:01:90")

    
    s2 = net.get("s2")
    s2.cmd("sysctl net.ipv4.ip_forward=1")
    # s2.cmd("suricata -c config/suricata2.yaml --pcap &")
    s2.cmd("ip route add 10.0.1.1 dev s2-eth0")
    s2.cmd("ip route add 10.0.1.4 dev s2-eth1")
    s2.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")
    s2.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    s2.cmd("arp -s 10.0.1.1 00:00:00:00:01:99")
    s2.cmd("arp -s 10.0.1.4 00:00:00:00:01:90")

    # Off loading test
    s1.cmd("sudo ethtool --offload s1-eth0 gro off gso off tso off")
    s1.cmd("sudo ethtool --offload s1-eth1 gro off gso off tso off")
    s2.cmd("sudo ethtool --offload s2-eth0 gro off gso off tso off")
    s2.cmd("sudo ethtool --offload s2-eth1 gro off gso off tso off")
    s2.cmd("sudo ethtool --offload s2-eth2 gro off gso off tso off")

    # Router directions
    r1 = net.get("r1")
    r2 = net.get("r2")
    r1.cmd("sudo ethtool --offload r1-eth1 gro off gso off tso off")
    r1.cmd("sudo ethtool --offload r1-eth2 gro off gso off tso off")
    r1.cmd("arp -s 10.0.1.4 00:00:00:00:01:90")
    r1.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    r1.cmd("ip route add default via 10.0.1.4")
    r1.cmd("arp -s 10.0.0.10 00:00:00:00:00:10")
    r1.cmd("arp -s 10.0.0.11 00:00:00:00:00:11")

    r2.cmd("arp -s 10.0.1.1 00:00:00:00:01:99")
    r2.cmd("ip route add default via 10.0.1.1")
    r2.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")

    # start with S2 ports down to prevent dupe traffic
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