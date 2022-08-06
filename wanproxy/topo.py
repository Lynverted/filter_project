from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import Node
from mininet.log import setLogLevel, info
import os

CLIENT_COUNT = 1
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
        clients = []
        self.serverswRules = []
        self.clientswRules = []

        info("*** Adding Switches\n")
        client_switch = self.addSwitch("cs1", dpid="101")
        backend_switch = self.addSwitch("bs1", dpid="202")

        info("*** Adding proxy\n")
        client_proxy = self.addHost("cproxy", ip="10.0.0.10/24", defaultRoute='via 10.0.0.1')
        server_proxy = self.addHost("bproxy", ip="10.0.1.20/24", defaultRoute='via 10.0.1.1')
        self.addLink(client_switch, client_proxy)
        self.addLink(backend_switch, server_proxy)

        info("*** Adding router\n")
        router = self.addHost("r1", cls=LinuxRouter, ip="10.0.0.1/24")
        self.addLink(client_proxy, router, params2={"ip": "10.0.0.1/24"})
        self.addLink(server_proxy, router, params2={"ip": "10.0.1.1/24"})
        # self.addLink(client_switch, router, params2={"ip": "10.0.0.1/24"})
        # self.addLink(backend_switch, router, params2={"ip": "10.0.1.1/24"})

        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+2)), defaultRoute='via 10.0.0.1'))
            self.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+2))

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(b+2)), defaultRoute='via 10.0.1.1'))
            self.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(b+2))

# Main method
def run():
    topo = clickTopo()
    net = Mininet(switch=OVSSwitch, build=False, topo=topo, controller=DefaultController, autoStaticArp=False, waitConnected=True)
    info("*** Starting Network\n")
    net.build()
    net.start()

    info("*** Starting HTTP Servers\n")
    backends = []
    for b in range(0, BACKEND_COUNT):
        backends.append(net.get('b' + str(b+1)))
        backends[b].cmd("sudo lighttpd -f ../backends/b"+str(b+2) + ".conf")
    #     backends[b].cmd("route add default gw 10.0.1.20 b{}-eth0".format(str(b+1)))
    
    # Add virt. IP to clients
    # clients = []
    # for x in range(0, CLIENT_COUNT):
    #     clients.append(net.get('c' + str(x+1)))
    #     clients[x].cmd("arp -s 10.0.0.20 00:00:00:00:00:FF")

    # for b in range(0, BACKEND_COUNT):
        #backends[b].cmd("arp -s 10.0.1.20 00:00:00:00:01:ff")
        #backends[b].cmd("arp -s 10.0.1."+str(b+1) + " 00:00:00:00:01:0"+str(b+1))

    info("*** Starting proxies\n")
    bproxy = net.get('bproxy')
    cproxy = net.get('cproxy')
    bproxy.cmd("ip route add 10.0.1.1 dev bproxy-eth1")
    cproxy.cmd("ip route add 10.0.0.1 dev cproxy-eth1")
    cproxy.cmd("ip route replace default via 10.0.0.1 dev cproxy-eth1")
    bproxy.cmd("ip route replace default via 10.0.1.1 dev bproxy-eth1")
    bproxy.cmd("wanproxy -c server.conf &")
    cproxy.cmd("wanproxy -c client.conf &")


    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo pkill -f "lighttpd"')


if __name__ == '__main__':
    setLogLevel('info')
    run()