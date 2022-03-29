from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os

CLIENT_COUNT = 1
BACKEND_COUNT = 1


def ClickMininet():

    net = Mininet(switch=OVSSwitch, build=False, topo=None, controller=DefaultController, autoStaticArp=False)

    clients = []
    info("*** Adding {} Clients\n".format(CLIENT_COUNT))
    client_switch = net.addSwitch("cs1")
    for c in range(0, CLIENT_COUNT):
        clients.append(net.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+1))))
        net.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+1), params1={"ip": "10.0.0.{}/24".format(str(c+1))})

    backends = []
    info("*** Adding {} Backends\n".format(BACKEND_COUNT))
    backend_switch = net.addSwitch("bs1")
    for b in range(0, BACKEND_COUNT):
        backends.append(net.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(b+1))))
        net.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(b+1), params1={"ip": "10.0.1.{}/24".format(str(c+1))})

    info("*** Adding Click\n")
    filter = net.addHost("click", ip=None)
    net.addLink(client_switch, filter, addr2="00:00:00:00:00:ff")
    net.addLink(backend_switch, filter, addr2="00:00:00:00:01:ff")

    net.addController(name='dc', controller=DefaultController)

    info("*** Starting Network\n")
    net.build()
    net.start()

    for b in range(0, BACKEND_COUNT):
        # backends[b].cmd("route add default gw 10.0.1.1 b{}-eth0".format(str(b+1)))
        backends[b].cmd("route add default gw 10.0.1.1 b{}-eth0".format(str(b+1)))
    
    # Add virt. IP to clients
    for x in range(0, CLIENT_COUNT):
        clients.append(net.get('c' + str(x+1)))
        clients[x].cmd("arp -s 10.0.0.20 00:00:00:00:00:FF")

    info("*** Starting Click Router\n")
    filter.cmd("click --unix /var/run/click -f ./NAT.cl & ")

    info("*** Starting HTTP Servers\n")
    for b in range(0, BACKEND_COUNT):
        backends[b].cmd("arp -s 10.0.1.254 00:00:00:00:01:ff")
        # backends[b].cmd("lighttpd -f ./backends/b{}.conf".format(str(b+1)))
        backends[b].cmd("python3 -m http.server 80 &")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo pkill -f "lighttpd"')


if __name__ == '__main__':
    setLogLevel('info')
    ClickMininet()



# Packet arrives at address of filter
# Anything on eth0 goes through pipeline
# Need some sort of print as it arrives on the eth0?
