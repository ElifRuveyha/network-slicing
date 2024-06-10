from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
import subprocess

class CustomTopology(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        # Create templates
        host_config = dict(inNamespace=True)
        link_config = dict()
        host_link_config = dict()

        # Add switches
        switches = {}
        for i in range(4):
            sconfig = {"dpid": "%016x" % (i + 1)}
            switches[i + 1] = self.addSwitch("s%d" % (i + 1), **sconfig)

        # Add hosts
        hosts = {}
        for i in range(8):
            hosts[i + 1] = self.addHost("h%d" % (i + 1), **host_config)

        # Add host links
        self.addLink(hosts[1], switches[1], **host_link_config)
        self.addLink(hosts[2], switches[1], **host_link_config)
        self.addLink(hosts[3], switches[2], **host_link_config)
        self.addLink(hosts[4], switches[2], **host_link_config)
        self.addLink(hosts[5], switches[3], **host_link_config)
        self.addLink(hosts[6], switches[3], **host_link_config)
        self.addLink(hosts[7], switches[4], **host_link_config)
        self.addLink(hosts[8], switches[4], **host_link_config)

        # Add switch links
        self.addLink(switches[1], switches[2], **link_config)
        self.addLink(switches[2], switches[3], **link_config)
        self.addLink(switches[2], switches[4], **link_config)
        self.addLink(switches[3], switches[4], **link_config)

if __name__ == "__main__":


    topo = CustomTopology()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )

    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    subprocess.call("./scripts/create_virtual_queues_drop_connections.sh")
    CLI(net)
    net.stop()
