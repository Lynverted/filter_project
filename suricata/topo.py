from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import Node
from mininet.log import setLogLevel, info
import os

CLIENT_COUNT = 2
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
        client_switch = self.addSwitch("cs1", dpid="101")
        backend_switch = self.addSwitch("bs1", dpid="202")
        suriC_switch = self.addSwitch("ss1", dpid="303")
        suriB_switch = self.addSwitch("ss2", dpid="404")

        info("*** Adding routers\n")
        client_router = self.addHost("r1", cls=LinuxRouter, ip="10.0.0.1/24")
        backend_router = self.addHost("r2", cls=LinuxRouter, ip="10.0.2.1/24")
        self.addLink(client_switch, client_router, params2={"ip": "10.0.0.1/24"})
        self.addLink(backend_switch, backend_router, params2={"ip": "10.0.2.1/24"})
        self.addLink(client_router, suriC_switch, params1={"ip": "10.0.1.1/24"})
        self.addLink(backend_router, suriB_switch, params1={"ip": "10.0.1.4/24"})

        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        clients = []
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+2)), defaultRoute='via 10.0.0.1'))
            self.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+2))

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.2.{}/24".format(str(b+2)), defaultRoute='via 10.0.2.1'))
            self.addLink(backends[b], backend_switch, addr1="00:00:00:00:02:0"+str(b+2))

        info("*** Adding Filter\n")
        # stick filter here

        info("*** Adding suricata\n")
        suri = self.addHost("s1", ip="10.0.1.2/24", defaultRoute='via 10.0.1.1')
        self.addLink(suri, suriC_switch)#, params1={"ip": "10.0.0.10/24"})
        self.addLink(suri, suriB_switch, params1={"ip": "10.0.1.3/24"})
        # self.addLink(suri, client_router, params2={"ip": "10.0.1.1/24"})
        # self.addLink(suri, backend_router, params1={"ip": "10.0.1.11/24"}, params2={"ip": "10.0.1.20/24"})

# Main method
def run():
    topo = clickTopo()
    net = Mininet(switch=OVSSwitch, build=False, topo=topo, controller=DefaultController, autoStaticArp=True, waitConnected=True)
    info("*** Starting Network\n")
    net.build()
    net.start()

    # c1 = net.addController( 'c1', controller=RemoteController, port=6633 )
    # for controller in net.controllers:
        # controller.start()
    # net.get("r1").start( [ c1 ])
    

    info("*** Starting HTTP Servers\n")
    backends = []
    for b in range(0, BACKEND_COUNT):
        backends.append(net.get('b' + str(b+1)))
        backends[b].cmd("sudo lighttpd -f ../backends/b"+str(b+1) + ".conf")
    #     backends[b].cmd("route add default gw 10.0.1.20 b{}-eth0".format(str(b+1)))
    
    # FF rules for the switches
    # clientsw = net.get("cs1")
    # clientsw.cmd("ovs-ofctl -OOpenFlow13 add-group cs1 'group_id=1,type=ff,bucket=watch_port:1,output:1,bucket=watch_port:2,output:2'")
    # clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_type=0x806,nw_dst=10.0.0.10,priority=2,actions=group:1'")
    # clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:00:FF,priority=1,actions=group:1'")

    s1 = net.get("s1")
    s1.cmd("suricata -c config/suricata.yaml --af-packet &")
    s1.cmd("ip route add 10.0.1.1 dev s1-eth0")
    s1.cmd("ip route add 10.0.1.4 dev s1-eth1")
    s1.cmd("ip route add 10.0.0.0/24 via 10.0.1.1")
    s1.cmd("ip route add 10.0.2.0/24 via 10.0.1.4")
    net.get("r1").cmd("ip route add 10.0.2.0/24 via 10.0.1.2")
    net.get("r2").cmd("ip route add 10.0.0.0/24 via 10.0.1.3")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo pkill -f "lighttpd"')
    os.system('sudo pkill -f "suricata"')


if __name__ == '__main__':
    setLogLevel('info')
    run()