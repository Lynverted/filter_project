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
        # net = Mininet(switch=OVSSwitch, build=False, topo=None, controller=DefaultController, autoStaticArp=False)
        clients = []
        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        client_switch = self.addSwitch("cs1")
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+1))))
            self.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+1), params1={"ip": "10.0.0.{}/24".format(str(c+1))})

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        backend_switch = self.addSwitch("bs1")
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(b+1)))) #, defaultRoute='via 10.0.1.20'))
            self.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(b+1), params1={"ip": "10.0.1.{}/24".format(str(b+1))})

        info("*** Adding Click\n")
        filter = self.addHost("click", ip=None)
        self.addLink(client_switch, filter, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        # self.addLink(backend_switch, filter, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")
        
        self.addLink(backend_switch, filter, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")
        # self.addLink(backend_router, backend_switch)

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
    net.get('click').cmd("click --unix /var/run/click -f ./NAT.cl & ")

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