#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 02/08/2018 3:15 PM
# @Author  : Jsen617
# @Site    : 
# @File    : simple_switch_13.py
# @Software: PyCharm
import Topo_Switch_13

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER,MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from collections import defaultdict
from ryu.lib.dpid import dpid_to_str,str_to_dpid

class simpleswitch13(Topo_Switch_13.TopoSwitch_13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self,*args,**kwargs):
        super(simpleswitch13,self).__init__(*args,**kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.full_path = defaultdict(lambda: defaultdict(lambda:None))
        #self.host_mac = {}
        #self.get_host_mac("hosts_mac.txt")
       # print(self.host_mac)
    
    
    def add_flows(self,datapath,priority,match,actions,buffer_id=None):
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        inst = [ofp_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]

        if buffer_id:
            mod = ofp_parser.OFPFlowMod(datapath,priority=priority,
                                        buffer_id=buffer_id,match=match,instructions=inst)
        else:
            mod = ofp_parser.OFPFlowMod(datapath,priority=priority,
                                        match=match,instructions=inst)
        datapath.send_msg(mod)
   
   
   
    def string_to_dpid(self,str):
        """
        str: "h1"
        return:"0000000000000001"
        """
        number_str = str[1:]
        number_str = hex(int(number_str))
        number_str = number_str[2:].zfill(16)
        return number_str                    



    def install_path(self, paths, dst, in_dpid, parser, ofproto, msg):
        nodes = list(paths.keys())
        out_port = 0
        self.logger.debug("try to install path for:%s",nodes)
        self.logger.debug("origin dpid is %s",in_dpid)
        for node in nodes:
            target_dpid = int(node[1:])
            if target_dpid == in_dpid:
                out_port = paths[node][1]
            target_in_port = paths[node][0]
            target_out_port = paths[node][1]
            target_actions = [parser.OFPActionOutput(target_out_port)]
            dst_ip = "10.0.0.%s"%dst[1:]
            print("dst_mac:",dst_ip)
            target_match = parser.OFPMatch(in_port=target_in_port,eth_type=0x0800,ipv4_dst=dst_ip)
            target_datapath = self._get_datapath(target_dpid)
            if target_datapath:
                self.add_flows(target_datapath,1,target_match,target_actions)
        
        return out_port#源节点的out port
    
    def get_host_mac(self,file_name):
        f = open(file_name)
        lines = f.readlines()
        i = 1
        for line in lines:
            line = line.strip()
            self.host_mac['h{}'.format(i)] = line
            i += 1




    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
    def switch_feature_handler(self,ev):
	   
        msg = ev.msg
        print ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        dpid = dp.id
        match = ofp_parser.OFPMatch()
        self.logger.info("add table-miss flow to Switch")
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER,ofp.OFPCML_NO_BUFFER)]

        self.add_flows(datapath=dp,priority=0,match=match,actions=actions)


    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
    def packet_in_handler(self,ev):
	#self.logger.info("pakcet in handler ev:",str(ev))
        
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated:only %s of %s bytes",ev.msg.msg_len,ev.msg.total_len)
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        in_port = msg.match["in_port"]
        #print("Flow inport:%s")%in_port
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        src = eth.src
        dst = eth.dst
        dpid = dp.id
        self.mac_to_port.setdefault(dpid,{})

        self.mac_to_port[dpid][src] = in_port
        #print("mac_to_port:",self.mac_to_port)
        if dst in self.mac_to_port[dpid]:
            outport = self.mac_to_port[dpid][dst]
        else:
            outport = ofp.OFPP_FLOOD

        #add flow to swtich to avoid packet in msg
        actions = [ofp_parser.OFPActionOutput(outport)]
        if outport != ofp.OFPP_FLOOD:
            self.logger.info("packet in %s %s %s %s",dpid,src,dst,in_port)
            match = ofp_parser.OFPMatch(in_port=in_port,eth_dst=dst)
            if msg.buffer_id != ofp.OFP_NO_BUFFER:
                self.add_flows(dp,1,match,actions,msg.buffer_id)
                return
            else:
                self.add_flows(dp,1,match,actions)
        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data
        out = ofp_parser.OFPPacketOut(datapath=dp,in_port=in_port,actions=actions,data=data,buffer_id=msg.buffer_id)

        dp.send_msg(out)





if __name__ == "__main__":
    pass
