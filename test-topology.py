from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import Node
from mininet.log import setLogLevel, info
import os

CLIENT_COUNT = 2
BACKEND_COUNT = 5

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

        info("*** Adding Click\n")
        nat = self.addHost("nat", ip=None)
        nat2 = self.addHost("nat2", ip=None)
        filter = self.addHost("filter", ip=None)
        self.addLink(client_switch, filter, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        self.addLink(client_switch, nat2, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        self.addLink(filter, nat) #, addr="00:00:00:00:00:dd")
        self.addLink(filter, nat2)
        self.addLink(backend_switch, nat, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")
        self.addLink(backend_switch, nat2, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")


        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+1))))
            self.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+1), params1={"ip": "10.0.0.{}/24".format(str(c+1))})

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(b+1)))) #, defaultRoute='via 10.0.1.20'))
            self.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(b+1), params1={"ip": "10.0.1.{}/24".format(str(b+1))})

        # self.addLink(client_switch, nat, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")

        # self.addLink(client_switch, filter, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")        
        # self.addLink(backend_switch, filter, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")

# Abstract out DPCTL commands
# class DSwitch( OVSSwitch ):
#     def start( self, controller ):
#         return OVSSwitch.start(self, controller)

#     def dpctl( self, *args ):
#         "Run ovs-ofctl command"
#         return self.cmd( 'ovs-ofctl -OOpenFlow13', args[ 0 ], self, *args[ 1: ] )

# Main method
def run():
    topo = clickTopo()
    net = Mininet(switch=OVSSwitch, build=False, topo=topo, controller=DefaultController, autoStaticArp=False, waitConnected=True)
    net.addController(name='dc', controller=DefaultController)
    info("*** Starting Network\n")
    net.build()
    net.start()

    backends = []
    for b in range(0, BACKEND_COUNT):
        backends.append(net.get('b' + str(b+1)))
        backends[b].cmd("route add default gw 10.0.1.20 b{}-eth0".format(str(b+1)))
    
    # Add virt. IP to clients
    clients = []
    for x in range(0, CLIENT_COUNT):
        clients.append(net.get('c' + str(x+1)))
        clients[x].cmd("arp -s 10.0.0.20 00:00:00:00:00:FF")

    info("*** Starting Click Router\n")
    net.get('nat').cmd("click --unix /var/run/click -f ./NAT.cl & ")
    net.get('nat2').cmd("click --unix /var/run/click2 -f ./NAT2.cl & ")
    net.get('filter').cmd("click --unix /var/run/click3 -f ./filter.cl & ")

    # FF rules for the switches
    clientsw = net.get("cs1")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-group cs1 'group_id=1,type=ff,bucket=watch_port:1,output:1,bucket=watch_port:2,output:2'")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_type=0x806,nw_dst=10.0.0.20,priority=2,actions=group:1'")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:00:FF,priority=1,actions=group:1'")

    serversw = net.get("bs1")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-group bs1 'group_id=1,type=ff,bucket=watch_port:1,output:1,bucket=watch_port:2,output:2'")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_type=0x806,nw_dst=10.0.0.20,priority=2,actions=group:1'")     # this is wrong
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:01:FF,priority=1,actions=group:1'")

    info("*** Starting HTTP Servers\n")
    for b in range(0, BACKEND_COUNT):
        backends[b].cmd("arp -s 10.0.1.254 00:00:00:00:01:ff")
        backends[b].cmd("arp -s 10.0.1."+str(b+1) + " 00:00:00:00:01:0"+str(b+1))
        backends[b].cmd("python3 -m http.server 80 &")
        # print("arp -s 10.0.1."+str(b+1) + " 00:00:00:00:01:0"+str(b+1))

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo pkill -f "lighttpd"')


if __name__ == '__main__':
    setLogLevel('info')
    run()