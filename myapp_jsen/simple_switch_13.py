#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 02/08/2018 3:15 PM
# @Author  : Jsen617
# @Site    : 
# @File    : simple_switch_13.py
# @Software: PyCharm
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER,MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class simpleswitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self,*args,**kwargs):
        super(simpleswitch13,self).__init__(*args,**kwargs)
        self.mac_to_port = {}
        self.datapaths = {}


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
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
    def switch_feature_handler(self,ev):
	#print ev.msg
        msg = ev.msg
        dp = msg.datapath
	#print dp
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

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
