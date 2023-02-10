from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch, DefaultController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import Node
from mininet.log import setLogLevel, info
import os
import time 

CLIENT_COUNT = 5
BACKEND_COUNT = 3

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
        lb1 = self.addSwitch("lb1", ip=None)
        lb2 = self.addSwitch("lb2", ip=None)
        filter = self.addHost("filter", ip=None)
        
        self.addLink(client_switch, filter)
        self.addLink(filter, lb1, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        self.addLink(client_switch, lb2, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        self.addLink(filter, lb2)
        self.addLink(backend_switch, lb1, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")
        self.addLink(backend_switch, lb2, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")

        # remove filter test
        # self.addLink(client_switch, lb1, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        # self.addLink(client_switch, lb2, addr1="00:00:00:00:00:ee", addr2="00:00:00:00:00:ff")
        # self.addLink(backend_switch, lb1, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")
        # self.addLink(backend_switch, lb2, addr1="00:00:00:00:01:ee", addr2="00:00:00:00:01:ff")

        info("*** Adding {} Clients\n".format(CLIENT_COUNT))
        for c in range(0, CLIENT_COUNT):
            clients.append(self.addHost("c"+str(c+1), ip="10.0.0.{}/24".format(str(c+1))))
            self.addLink(clients[c], client_switch, addr1="00:00:00:00:00:0"+str(c+1), params1={"ip": "10.0.0.{}/24".format(str(c+1))})

        backends = []
        info("*** Adding {} Backends\n".format(BACKEND_COUNT))
        for b in range(0, BACKEND_COUNT):
            backends.append(self.addHost("b"+str(b+1), ip="10.0.1.{}/24".format(str(b+1))))
            self.addLink(backends[b], backend_switch, addr1="00:00:00:00:01:0"+str(b+1), params1={"ip": "10.0.1.{}/24".format(str(b+1))})

# WRK instances - output destination/file, number of clients, duration
def wrk(clientsList, outFile, clients, dur):
    popens = {}
    for x in range(CLIENT_COUNT):
        log = open(outFile, 'a')
        log.flush()
        popens[x] = clientsList[x].popen("wrk -t 2 -c " + str(clients) + " -d " + str(dur) + " http://10.0.0.20/ &", stdout=log, shell=True, close_fds=True)
        # http://10.1.0.20/bunny_1s_8000kbit/size.html
        # http://10.1.0.20/index.html
    print("Running clients")
    for x in range(CLIENT_COUNT):
         popens[x].communicate()
    print("all complete")

# GST instances - output destination/file, list of clients
def video(clientsList, folder):
    print("Running Locust instances...")
    popens = {}
    for x in range(CLIENT_COUNT):
        popens[x] = clientsList[x].popen("gst-launch-1.0 -vvv playbin uri='http://10.0.0.20/bunny.mpd' \
            video-sink=fakevideosink 2>&1 | tee >(ts '%Y-%m-%d %H:%M:%.S' > /home/lyn/filter/output/gst/" \
                + folder + "/raw" + str(x) + ".log) &", shell=True)
        time.sleep(1)
        if x % 20 == 0 and x != 0:
           print(x)
           time.sleep(40)
    print("Flows active")
    for x in range(CLIENT_COUNT):
        popens[x].communicate()
    print("All complete.")

# Main method
def run():
    topo = clickTopo()
    net = Mininet(switch=OVSSwitch, build=False, topo=topo, controller=None, autoStaticArp=False, waitConnected=False)
    info("*** Starting Network\n")
    net.build()
    net.start()

    # LB setups
    lb1 = net.get("lb1")
    lb2 = net.get("lb2")
    os.system("ovs-ofctl -O OpenFlow11 add-group lb1 group_id=1,type=select,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:01,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.1,output:2,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:02,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.2,output:2,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:03,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.3,output:2")
    # ,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:04,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.4,output:2
    # ,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:05,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.5,output:2")
    lb1.cmd("ovs-ofctl add-flow lb1 ip,nw_dst=10.0.0.20,tcp,tp_dst=80,actions=group:1")
    os.system("ovs-ofctl -O OpenFlow11 add-group lb2 group_id=1,type=select,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:01,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.1,output:3,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:02,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.2,output:3,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:03,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.3,output:3")
    lb2.cmd("ovs-ofctl add-flow lb2 ip,nw_dst=10.0.0.20,tcp,tp_dst=80,actions=group:1")

    # Backend setup part 1
    backends = []
    for b in range(0, BACKEND_COUNT):
        backends.append(net.get('b' + str(b+1)))
        backends[b].cmd("route add default gw 10.0.1.254 b{}-eth0".format(str(b+1)))

    # FF rules for the switches
    clientsw = net.get("cs1")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-group cs1 'group_id=1,type=ff,bucket=watch_port:1,output:1,bucket=watch_port:2,output:2'")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_type=0x806,nw_dst=10.0.0.20,priority=2,actions=group:1'")
    clientsw.cmd("ovs-ofctl -OOpenFlow13 add-flow cs1 'dl_dst=00:00:00:00:00:FF,priority=1,actions=group:1'")

    serversw = net.get("bs1")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-group bs1 'group_id=1,type=ff,bucket=watch_port:1,output:1,bucket=watch_port:2,output:2'")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_type=0x806,nw_dst=10.0.0.20,priority=2,actions=group:1'")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 'dl_dst=00:00:00:00:01:FF,priority=1,actions=group:1'")
    serversw.cmd("ovs-ofctl -OOpenFlow13 add-flow bs1 priority=0,actions=goto_table=1")

    # Return paths when swapping back
    serversw.cmd("ovs-ofctl add-flow bs1 'in_port=2,ip,tcp,priority=10,actions=learn( \
        priority=11,idle_timeout=60,dl_type=0x800,nw_proto=6,dl_dst=dl_src,dl_src=dl_dst,nw_dst=nw_src, \
        nw_src=nw_dst,tp_dst=tp_src,tp_src=tp_dst,output=NXM_OF_IN_PORT[]),goto_table=1'")
     
    # Add virt. IP to clients
    clients = []
    for x in range(0, CLIENT_COUNT):
        clients.append(net.get('c' + str(x+1)))
        clients[x].cmd("arp -s 10.0.0.20 00:00:00:00:00:FF")
        lb1.cmd("ovs-ofctl add-flow lb1 ip,nw_dst=10.0.0.%d,priority=1,actions=mod_nw_src:10.0.0.20,mod_dl_src:00:00:00:00:00:ff,mod_dl_dst:00:00:00:00:00:0%d,output:1"%(x+1, x+1))
        lb1.cmd("ovs-ofctl add-flow cs1 dl_dst=00:00:00:00:00:0%d,priority=1,actions=output:%d"%(x+1, x+3))
        lb2.cmd("ovs-ofctl add-flow lb2 ip,nw_dst=10.0.0.%d,priority=1,actions=mod_nw_src:10.0.0.20,mod_dl_src:00:00:00:00:00:ff,mod_dl_dst:00:00:00:00:00:0%d,output:1"%(x+1, x+1))

    # Click 
    info("*** Starting Click Router\n")
    net.get('filter').cmd("sudo click --unix /var/run/click -f ./filter.cl & ")

    # Removing large packet sending for click MTU requirements
    for i in range(len(net.get('lb1').intfList())):
        net.get('lb1').cmd("sudo ethtool --offload lb1-eth" + str(i) + " tso off gso off gro off")
    for i in range(len(net.get('lb2').intfList())):
        net.get('lb2').cmd("sudo ethtool --offload lb2-eth" + str(i) + " tso off gso off gro off")
    for i in range(len(net.get('filter').intfList())):
        net.get('filter').cmd("sudo ethtool --offload filter-eth" + str((i+1)) + " tso off gso off gro off")

    # Backend setup part 2
    for b in range(0, BACKEND_COUNT):
        backends[b].cmd("arp -s 10.0.1.254 00:00:00:00:01:ff")
        backends[b].cmd("arp -s 10.0.1."+str(b+1) + " 00:00:00:00:01:0"+str(b+1))
        backends[b].cmd("sudo lighttpd -f ../backends/b"+str(b+1) + ".conf")
        serversw.cmd("ovs-ofctl add-flow bs1 table=1,dl_dst=00:00:00:00:01:0%d,priority=1,actions=output:%d"%(b+1, b+3))

    # For non-copying testing purposes
        # net.get('lb2').cmd("sudo ip link set lb2-eth1 down")   
    
    # info("*** Running GST instances\n")
        # experName = "FO"
        # video(clients, experName)
        # os.system('sudo java -jar gStreamerParser/out/parser.jar ' + experName + ' ' + str(CLIENT_COUNT))
        # os.system('sudo python3 scripts/sort-gst.py ' + experName + ' ' + str(CLIENT_COUNT))
        # os.system('cat results/gst/' + experName +'/combined.txt | jq')

    # info("*** Running WRK instances\n")
        # wrk(clients, "output/fuck.txt", 75, 120)

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping Network\n")
    net.stop()
    os.system('sudo mn -c')
    os.system('sudo rm /var/run/click')

if __name__ == '__main__':
    setLogLevel('info')
    run()


# gst-launch-1.0 -vvv playbin uri='http://10.0.0.20/bunny.mpd' video-sink=fakevideosink 2>&1 | tee >(ts '%Y-%m-%d %H:%M:%.S' > /home/lyn/filter/output/gst/raw.log)
# ovs-ofctl -OOpenFlow13 add-group lb1 group_id=1,type=select,bucket=weight=50,actions=mod_dl_dst:00:00:00:00:01:01,mod_dl_src:00:00:00:00:01:ff,mod_nw_dst:10.0.1.1,output:2