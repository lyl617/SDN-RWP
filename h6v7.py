#!/usr/bin/python

"""
topology with 6 switches and 7 hosts
"""

from mininet.cli import CLI
from mininet.topo import Topo 
from mininet.net import Mininet 
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import RemoteController

class HRTopo(Topo):
    def __init__(self):
        "create topology"

        Topo.__init__(self)

        # hosts = []
        # #add hosts
        # num_hosts = 6
        # for i in range(num_hosts):
        #     host = self.addHost('h{}'.format(i+1))
        #     hosts.append(host)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')

        # switches = []
        # num_switches = 7
        # for i in range(num_switches):
        #     sw = self.addSwitch('s{}'.format(i+1))
        #     switches.append(sw)
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        s7 = self.addSwitch('s7')
        #add links between hosts and switches
        self.addLink(h1,s1)# h1-eth0 <-> s1-eth1
        self.addLink(h2,s5)# h2-eth0 <-> s5-eth1
        self.addLink(h3,s5)# h3-eth0 <-> s5-eth2
        self.addLink(h4,s5)# h4-eth0 <-> s5-eth3
        self.addLink(h5,s3)# h5-eth0 <-> s3-eth1
        self.addLink(h6,s3)# h6-eth0 <-> s3-eth2

        #add links between switches,with bandwidth 100Mbps,1Mbps=128KB/s
        self.addLink( s1, s2, bw=1000 )# s1-eth2 <-> s2-eth1
        self.addLink( s1, s6, bw=1000 )# s1-eth3 <-> s6-eth1
        self.addLink( s1, s7, bw=1000 )# s1-eth4 <-> s7-eth1
        self.addLink( s2, s3, bw=1000 )# s2-eth2 <-> s3-eth3
        self.addLink( s2, s5, bw=1000 )# s2-eth3 <-> s5-eth4
        self.addLink( s3, s4, bw=1000 ) # s3-eth4 <-> s4-eth1
        self.addLink( s3, s7, bw=1000 ) # s3-eth5 <-> s7-eth2
        self.addLink( s4, s5, bw=1000 ) # s4-eth2 <-> s5-eth5
        self.addLink( s5, s6, bw=1000 ) # s5-eth6 <-> s6-eth2

def run():
    "create and configure network"
    topo = HRTopo()
    mycontroller = RemoteController("myController", ip = "127.0.0.1")
    net = Mininet( topo = topo, link = TCLink, controller = mycontroller)

    #set interface IP and Mac addresses for hosts
    h1 = net.get('h1')
    h1.intf('h1-eth0').setIP('10.0.0.1',24)
    h1.intf( 'h1-eth0' ).setMAC( '0A:00:01:02:00:00' )

    h2 = net.get( 'h2' )
    h2.intf( 'h2-eth0' ).setIP( '10.0.0.2', 24 )
    h2.intf( 'h2-eth0' ).setMAC( '0A:00:02:02:00:00' )

    h3 = net.get( 'h3' )
    h3.intf( 'h3-eth0' ).setIP( '10.0.0.3', 24 )
    h3.intf( 'h3-eth0' ).setMAC( '0A:00:03:02:00:00' )

    h4 = net.get( 'h4' )
    h4.intf( 'h4-eth0' ).setIP( '10.0.0.4', 24 )
    h4.intf( 'h4-eth0' ).setMAC( '0A:00:04:02:00:00' )

    h5 = net.get( 'h5' )
    h5.intf( 'h5-eth0' ).setIP( '10.0.0.5', 24 )
    h5.intf( 'h5-eth0' ).setMAC( '0A:00:05:02:00:00' )

    h6 = net.get( 'h6' )
    h6.intf( 'h6-eth0' ).setIP( '10.0.0.6', 24 )
    h6.intf( 'h6-eth0' ).setMAC( '0A:00:06:02:00:00' )

    #set interface mac address for switches (NOTE: IP addresses are not assigned to switch interfaces)

    net.start()

    #add arp cache entries for hosts
    h1.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h1-eth0' )
    h1.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h1-eth0' )
    h1.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h1-eth0' )
    h1.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h1-eth0' )
    h1.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h1-eth0' )
    h1.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h1-eth0' )

    h2.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h2-eth0' )
    h2.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h2-eth0' )
    h2.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h2-eth0' )
    h2.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h2-eth0' )
    h2.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h2-eth0' )
    h2.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h2-eth0' )

    h3.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h3-eth0' )
    h3.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h3-eth0' )
    h3.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h3-eth0' )
    h3.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h3-eth0' )
    h3.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h3-eth0' )
    h3.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h3-eth0' )

    h4.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h4-eth0' )
    h4.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h4-eth0' )
    h4.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h4-eth0' )
    h4.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h4-eth0' )
    h4.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h4-eth0' )
    h4.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h4-eth0' )

    h5.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h5-eth0' )
    h5.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h5-eth0' )
    h5.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h5-eth0' )
    h5.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h5-eth0' )
    h5.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h5-eth0' )
    h5.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h5-eth0' )

    h6.cmd( 'arp -s 10.0.0.1 0A:00:01:02:00:00 -i h6-eth0' )
    h6.cmd( 'arp -s 10.0.0.2 0A:00:02:02:00:00 -i h6-eth0' )
    h6.cmd( 'arp -s 10.0.0.3 0A:00:03:02:00:00 -i h6-eth0' )
    h6.cmd( 'arp -s 10.0.0.4 0A:00:04:02:00:00 -i h6-eth0' )
    h6.cmd( 'arp -s 10.0.0.5 0A:00:05:02:00:00 -i h6-eth0' )
    h6.cmd( 'arp -s 10.0.0.6 0A:00:06:02:00:00 -i h6-eth0' )

    # Open Mininet Command Line Interface
    CLI(net)

    # Teardown and cleanup
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()