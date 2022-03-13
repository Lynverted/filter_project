from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

CLIENT_COUNT = 1
BACKEND_COUNT = 5


def ClickMininet():

    net = Mininet(switch=OVSSwitch, build=False, topo=None, controller=DefaultController, autoStaticArp=False)

    clients = []
    info("*** Adding {} Clients\n".format(CLIENT_COUNT))
    client_switch = net.addSwitch("cs1")
    for c in range(0, CLIENT_COUNT):
        clients.append(net.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+2))))
        net.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+2), params1={"ip": "10.0.0.{}/24".format(str(c+2))})

    backends = []
    info("*** Adding {} Backends\n".format(BACKEND_COUNT))
    backend_switch = net.addSwitch("bs1")
    for b in range(0, BACKEND_COUNT):
        backends.append(net.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(c+2))))
        net.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(c+2), params1={"ip": "10.0.1.{}/24".format(str(c+2))})

    info("*** Adding Loadbalancers\n".format(BACKEND_COUNT))
    click_lb = net.addHost("click", ip="10.0.0.1/24")
    net.addLink(client_switch, click_lb, addr2="00:00:00:00:00:01", params2={"ip": "10.0.0.1/24"})
    net.addLink(backend_switch, click_lb, addr2="00:00:00:00:01:01", params2={"ip": "10.0.1.1/24"})

    net.addController(name='dc', controller=DefaultController)

    info("*** Starting Network\n")
    net.build()
    net.start()

    for b in range(0, BACKEND_COUNT):
        backends[b].cmd("route add default gw 10.0.1.1 b{}-eth0".format(str(b+1)))

    info("*** Starting Click Router\n")
    click_lb.cmd("click --unix /var/run/click -f ./lb.click & ")

    info("*** Starting HTTP Servers\n")
    for b in range(0, BACKEND_COUNT):
        # backends[b].cmd("lighttpd -f ./backends/b{}.conf".format(str(b+1)))
        backends[b].cmd("python3 -m http.server 80 &")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    ClickMininet()
