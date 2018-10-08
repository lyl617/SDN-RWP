# coding:utf-8
# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Usage example
1. Run this application:
$ ryu-manager  --observe-links ospf.switch_13.py


2. Switch struct

please see ryu/topology/switches.py

msg struct: 
{'dpid': '0000000000000001', 
'ports': [
            {'dpid': '0000000000000001', 
            'hw_addr': 'b6:b8:0b:3f:e5:86', 
            'name': 's1-eth1', 
            'port_no': '00000001'}, 
            {'dpid': '0000000000000001', 
            'hw_addr': '2e:fa:67:bd:f3:b2', 
            'name': 's1-eth2', 
            'port_no': '00000002'}
        ]
}

2. Link struct

please see ryu/topology/switches.py

note: two node will get two link.

eg: s1--s2  will get link: s1 -> s2 and link: s2->s1

msg struct

{
'dst': {'port_no': '00000001', 
         'name': 's2-eth1', 
         'hw_addr': '52:9c:f6:6d:d3:5f', 
         'dpid': '0000000000000002'}, 
'src': {'port_no': '00000001', 
        'name': 's1-eth1', 
        'hw_addr': '22:33:5a:65:de:62', 
        'dpid': '0000000000000001'}
}

3. Host struct



3. Topology change is notified:
< {"params": [{"ports": [{"hw_addr": "56:c7:08:12:bb:36", "name": "s1-eth1", "port_no": "00000001", "dpid": "0000000000000001"}, {"hw_addr": "de:b9:49:24:74:3f", "name": "s1-eth2", "port_no": "00000002", "dpid": "0000000000000001"}], "dpid": "0000000000000001"}], "jsonrpc": "2.0", "method": "event_switch_enter", "id": 1}
> {"id": 1, "jsonrpc": "2.0", "result": ""}
< {"params": [{"ports": [{"hw_addr": "56:c7:08:12:bb:36", "name": "s1-eth1", "port_no": "00000001", "dpid": "0000000000000001"}, {"hw_addr": "de:b9:49:24:74:3f", "name": "s1-eth2", "port_no": "00000002", "dpid": "0000000000000001"}], "dpid": "0000000000000001"}], "jsonrpc": "2.0", "method": "event_switch_leave", "id": 2}
> {"id": 2, "jsonrpc": "2.0", "result": ""}
...
""" 


from operator import attrgetter
import Traffic_Monitor
import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from collections import defaultdict
from ryu.topology import event
from ryu.topology.switches import *
from ryu.lib.dpid import dpid_to_str, str_to_dpid
import algorithms
import random
import threading
import json


# this mutex is for self.hosts
# when EventHostAdd is occur, it needs add host to self.hosts
# but def _update_host_list also has to update self.hosts
# def _update_host_list is working at other thread, so needs mutex
mutex = threading.Lock()




class TopoSwitch_13(simple_switch_13.simpleswitch13):

    def __init__(self, *args, **kwargs):
        super(TopoSwitch_13, self).__init__(*args, **kwargs)
        self.monitor_thread = hub.spawn(self._monitor)
        
        #---topology---------
        self.switches = {}
        self.port_state = {}
        self.links = defaultdict(lambda: None)
        self.hosts = HostState()
        
        self.switch_macs = set()
        self.hosts_num = 6#numbers of hosts
        self.ratio = 3 #ratio of matching
        self.hosts_pair = self.get_hosts_pair()
        # links has no weight!!
        self.net_topo = defaultdict(lambda: defaultdict(lambda: None))

        #--------------


        self.arp_table = {}

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
                #print("MAIN_datapaths:",self.datapaths)
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
                #print("DEAD_datapaths:",self.datapaths)

    def install_path(self, paths, dst, in_dpid, parser, ofproto, msg):
        nodes = list(paths.keys())
        out_port = 0
        self.logger.debug("try to install path for:%s",nodes)
        self.logger.debug("origin dpid is %s",in_dpid)
        for node in nodes:
            #node_str = self.string_to_dpid(node)
            #target_dpid = str_to_dpid(node_str)
            target_dpid = int(node[1:])
            #print("target_dpid:",target_dpid)
            if target_dpid == in_dpid:
                out_port = paths[node][1]
            target_in_port = paths[node][0]
            target_out_port = paths[node][1]

            target_actions = [parser.OFPActionOutput(target_out_port)]
            #dst_mac = self.host_mac[dst]
            dst_ip = "10.0.0.%s"%dst[1:]
            print("dst_mac:",dst_ip)
            target_match = parser.OFPMatch(in_port=target_in_port,eth_type=0x0800,ipv4_dst=dst_ip)
            target_datapath = self._get_datapath(target_dpid)
            #print("target_datapath:",target_datapath)
            # if msg.buffer_id != ofproto.OFP_NO_BUFFER:
            #     self.add_flows(target_datapath,1,target_match,target_actions,msg.buffer_id)
            # else:
            if target_datapath:
                self.add_flows(target_datapath,1,target_match,target_actions)
        
        return out_port#源节点的out port

    def get_detail_path(self,src,dst):
        return algorithms.get_path(src, dst, self.full_path, self.net_topo)
        
    def get_hosts_pair(self):
        hosts_pair = defaultdict(list)
        hosts = []
        for i in range(self.hosts_num):
            hosts.append('h{}'.format(i+1))
        for h in hosts:
            for i in range(self.ratio):
                index_host = random.randint(0,self.hosts_num-1)
                while hosts[index_host] in hosts_pair[h]\
                or hosts[index_host] == h:
                    index_host = random.randint(0,self.hosts_num-1)
                hosts_pair[h].append(hosts[index_host])
        return hosts_pair

    def string_to_dpid(self,str):
        """
        str: "h1"
        return:"0000000000000001"
        """
        number_str = str[1:]
        number_str = hex(int(number_str))
        number_str = number_str[2:].zfill(16)
        return number_str    

    @set_ev_cls(event.EventSwitchEnter)
    def _event_switch_enter_handler(self,ev):
        msg = ev.switch
       
        dp = msg.dp
        dpid = dp.id
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        #print(dpid)
    #    msg struct: 
    #    {'dpid': '0000000000000001', 
    #    'ports': [
    #               {'dpid': '0000000000000001', 
    #               'hw_addr': 'b6:b8:0b:3f:e5:86', 
    #               'name': 's1-eth1', 
    #               'port_no': '00000001'}, 
    #               {'dpid': '0000000000000001', 
    #               'hw_addr': '2e:fa:67:bd:f3:b2', 
    #               'name': 's1-eth2', 
    #               'port_no': '00000002'}
    #             ]
    #     }

        
        self._register(msg.dp)
        
        for src,dsts in self.hosts_pair.items():
            self.logger.info('src:  %s'%src)
            # in_dpid = str_to_dpid(src)
            # if dpid == in_dpid:
            for dst in dsts:
                """
                {'e10': [4, 1], 'a3': [2, 4], 'a5': [4, 2], 'e8': [1, 4], 'c2': [3, 1]}
                """
                paths = self.get_detail_path(src, dst)
                print("src:%s,dst:%s"%(src,dst))
                print("path:",paths)
                for sw in paths.keys():
                    number_sw = self.string_to_dpid(sw)
                    in_dpid = str_to_dpid(number_sw)
                    #in_dpid = int(sw[1:])
                    if dpid == in_dpid:
                        print("install path")
                        out_port = self.install_path(paths,dst,in_dpid,ofp_parser,ofp,msg)
                print("------------------------")
            print("********************")
        self.logger.info('Switch enter: %s',dpid_to_str(msg.dp.id))


    def _register(self,dp):
        assert dp.id is not None
        self.switches[dp.id] = dp
        if dp.id not in self.port_state:
            self.port_state[dp.id] = PortState()
            # print("register ports: ",dp.ports.values())
            for port in dp.ports.values():
                self.switch_macs.add(port.hw_addr)
                self.port_state[dp.id].add(port.port_no, port)

    def _unregister(self, dp):
        if dp.id in self.switches:
            if (self.switches[dp.id] == dp):
                del self.switches[dp.id]
                del self.port_state[dp.id]


    #- Reminder: switch and datapath is different
    #- switch class is in ryu.topology.switches.Swtich, it contains 
    #- the switch's dpid, port etc.
    #- And the datapath class is in ryu.controller.Datapath
    #- datapath is a class to describe an OpenFlow switch connected to this controller.
    #- it's attributes please see ryu.controller.Datapath
    
    def _get_switch(self, dpid):
        if dpid in self.switches:
            switch = Switch(self.switches[dpid])
            for ofpport in self.port_state[dpid].values():
                switch.add_port(ofpport)
            return switch
    
    def _get_datapath(self,dpid):
        #print("datapahts:",self.datapaths)
        if dpid in self.datapaths:
            return self.datapaths[dpid]

    # def _is_edge_port(self, port):
    #     if port.hw_addr in self.switch_macs:
    #         return False
    #     return True
        # for link in self.links:
        #     if port == link.src or port == link.dst:
        #         return False

        # return True

    def _is_edge_port(self, mac):
        if mac in self.switch_macs:
            return False
        return True

    # @set_ev_cls(event.EventSwitchLeave)
    # def _event_switch_leave_handler(self, ev):
    #     self.all_switches._unregister(ev.switch.dp)
    #     self.logger.info('Switch Leave: %s',dpid_to_str(ev.switch.dp.id))

    @set_ev_cls(event.EventLinkAdd)
    def _event_link_add_handler(self, ev):
        msg = ev.link
        if self.links[msg] is not None:
            return
        self.links[msg] = 1
        self.logger.info('event_link_add ')

    def _update_host_list(self):

        if mutex.acquire():
        
            for host_mac in self.hosts:
                host = self.hosts[host_mac]
                port = host.port
                if not self._is_edge_port(host.mac):
                    del(self.hosts[host_mac])
                    mutex.release()
                    return
            mutex.release()    

    # @handler.set_ev_cls(event.EventLinkDelete)
    # def _event_link_delete_handler(self, ev):
    #     msg = ev.link.to_dict()
        
    #     print('event_link_delete')
    #     print(msg)

    @set_ev_cls(event.EventHostAdd)
    def _event_host_add_handler(self, ev):

        msg = ev.host
        in_port = msg.port
        mac = msg.mac

        if self._is_edge_port(mac):
            if mutex.acquire():
                self.hosts.add(msg)
                mutex.release()
            src_dpid = msg.mac
            for ip4 in msg.ipv4:
                self.arp_table[ip4] = src_dpid
            self.logger.info('event_host_add %s',src_dpid)

    def _monitor(self):
        while True:
            self._update_host_list()
            self._update_net_topo()
            #print("net-topo:",self.net_topo)
            self.logger.info("all hosts: %s",[host for host in self.hosts])
            for dp in self.datapaths.values():
                self._request_stats(dp)
            # self.logger.info("link number is: %s",len(self.links))
            # self.print_topo()
            hub.sleep(50)

    def _request_stats(self,datapath):
        self.logger.debug('send stats request: %016x',datapath.id)
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        #req = ofp_parser.OFPPortStatsRequest(datapath,0,ofp.OFPP_ANY)
        #datapath.send_msg(req)

        req = ofp_parser.OFPTableStatsRequest(datapath,0)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPTableStatsReply,MAIN_DISPATCHER)
    def table_stats_reply_handler(self,ev):
        body = ev.msg.body
        i = 1
        self.logger.info("table-stats")
        self.logger.info('datapath table-id ' 'active-count lookup-count matched-count ')
        #self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('table_id')):
            if i == 1:
                self.logger.info('%016x %8x %8d %8d %8d',
                                                    ev.msg.datapath.id, stat.table_id,
                                                    stat.active_count,stat.lookup_count,
                                                    stat.matched_count)
            else:
                break
            i += 1
        self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')

    @set_ev_cls(ofp_event.EventOFPPortStatsReply,MAIN_DISPATCHER)
    def port_stats_reply_handler(self,ev):
        body = ev.msg.body
        self.logger.info('datapath port ' 'rx-pkts rx-bytes rx-error ' 'tx-pkts tx-bytes tx-error')
        self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
                self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                                                                              ev.msg.datapath.id, stat.port_no,
                                                                              stat.rx_packets, stat.rx_bytes,
                                                                              stat.rx_errors, stat.tx_packets,
                                                                              stat.tx_bytes, stat.tx_errors)
            
        self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')
        # ports=[]
        # for stat in ev.msg.body:
        #     ports.append('port_no=%d '
        #              'rx_packets=%d tx_packets=%d '
        #              'rx_bytes=%d tx_bytes=%d '
        #              'rx_dropped=%d tx_dropped=%d '
        #              'rx_errors=%d tx_errors=%d '
        #              'rx_frame_err=%d rx_over_err=%d rx_crc_err=%d '
        #              'collisions=%d duration_sec=%d duration_nsec=%d' %
        #              (stat.port_no,
        #               stat.rx_packets, stat.tx_packets,
        #               stat.rx_bytes, stat.tx_bytes,
        #               stat.rx_dropped, stat.tx_dropped,
        #               stat.rx_errors, stat.tx_errors,
        #               stat.rx_frame_err, stat.rx_over_err,
        #               stat.rx_crc_err, stat.collisions,
        #               stat.duration_sec, stat.duration_nsec))
        # self.logger.debug('PortStats: %s',ports)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply,MAIN_DISPATCHER)
    def flow_stats_reply_handler(self,ev):
        flows = []
        i = 0
        self.logger.info('flow-stats')
        self.logger.info('datapath table-id  priority ' 'idle_timeout hard_timeout flags ' 'cookie packet_count byte_count')
        #self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')
        for stat in ev.msg.body:
            #self.logger.info('No %s flow stats',str(i+1))
            #self.logger.info('%s',json.dumps(ev.msg.to_jsondict(),ensure_ascii=True,indent=3,sort_keys=True))
            
            self.logger.info('%016x %8d %8x %8d %8d %8d %8d %8d %8d', ev.msg.datapath.id, stat.table_id, stat.priority,
                                                                    stat.idle_timeout, stat.hard_timeout,
                                                                    stat.flags, stat.cookie, stat.packet_count,
                                                                    stat.byte_count)
            i+=1
        self.logger.info('---------------- -------- ' '-------- -------- -------- ' '-------- -------- --------')
    def _update_net_topo(self):

        for link in self.links:
            src_port = link.src.to_dict()
            dst_port = link.dst.to_dict()
            src_mac = src_port['dpid']
            dst_mac = dst_port['dpid']
            self.net_topo[src_mac][dst_mac] = link.to_dict()
 
        for host_mac in self.hosts:
            host = self.hosts[host_mac].to_dict()
            switch_port = host['port']
            dpid = switch_port['dpid']

            host_port = {'hw_addr': host['mac'],
                        'dpid':host['mac'],
                        'port_no':'00000001',
                        'name':'host'}
            hostid = host['mac']

            link_info_1 = {'src':host_port,'dst':switch_port}
            link_info_2 = {'src':switch_port,'dst':host_port}

            self.net_topo[hostid][dpid] = link_info_1
            self.net_topo[dpid][hostid] = link_info_2


    def print_topo(self):

        self.logger.info("--------------")
        for node in self.net_topo:
            self.logger.info("node--> %s",node)
            for sub in self.net_topo[node]:
                if self.net_topo[node][sub] is not None:
                    self.logger.info("       sub: %s",sub)
        self.logger.info("--------------")