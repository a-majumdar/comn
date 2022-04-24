from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet.ether_types import ETH_TYPE_IP

class L4Mirror14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4Mirror14, self).__init__(*args, **kwargs)
        self.ht = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, psr.OFPMatch(), acts)

    def add_flow(self, dp, prio, match, acts, buffer_id=None):
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
        ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
        mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        in_port, pkt = (msg.match['in_port'], packet.Packet(msg.data))
        dp = msg.datapath
        ofp, psr, did = (dp.ofproto, dp.ofproto_parser, format(dp.id, '016d'))
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        iph = pkt.get_protocols(ipv4.ipv4)
        tcph = pkt.get_protocols(tcp.tcp)

        out_port = 2 if in_port == 1 else 1
        #
        # write your code here
        # tcp_header = tcph[0] if len(tcph) != 0 else None
        # ip_header = iph[0] if len(iph) != 0 else None
        # add_flow_flag = False
        # acts = [psr.OFPActionOutput(out_port)]
        # if tcp_header is not None and ip_header is not None:
        #     if in_port == 1:
        #         add_flow_flag = True
        #     elif in_port == 2:
        #         address = (ip_header.src, ip_header.dst, tcp_header.src_port, tcp_header.dst_port)
        #         if tcp_header.has_flags(tcp.TCP_SYN) and not tcp_header.has_flags(tcp.TCP_FIN) and not tcp_header.has_flags(tcp.TCP_RST):
        #             self.ht[address] = 1
        #             acts.append(psr.OFPActionOutput(3))
        #         elif address in self.ht:
        #             self.ht[address] = self.ht[address] + 1
        #             acts.append(psr.OFPActionOutput(3))
        #         else:
        #             return
        #         if address in self.ht and self.ht[address] >= 10:
        #             self.ht.pop(address, None)
        #             add_flow_flag = True
        # if add_flow_flag:
        #     mtc = psr.OFPMatch(in_port=in_port, ip_proto = ip_header.proto, ipv4_src=ip_header.src, ipv4_dst = ip_header.dst, eth_type=eth.ethertype, tcp_src=tcp_header.src_port, tcp_dst=tcp_header.dst_port)
        #     self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
        #     if msg.buffer_id != ofp.OFP_NO_BUFFER:
        #         return
        acts = [psr.OFPActionOutput(out_port)]
        tproto = tcph[0] if len(tcph) != 0 else None
        nproto = iph[0] if len(iph) != 0 else None
        if tproto is not None and nproto is not None:
            sip, dip = (nproto.src, nproto.dst)
            sport, dport = (tproto.src_port, tproto.dst_port)
            flow = (sip, dip, sport, dport)
            match = psr.OFPMatch(in_port=in_port, ip_proto=nproto.proto, ipv4_src=sip, ipv4_dst=dip, eth_type=eth.ethertype, tcp_src=sport, tcp_dst=dport)
            if in_port == 1:
                self.add_flow(dp, 1, match, acts, msg.buffer_id)
                if msg.buffer_id != ofp.OFP_NO_BUFFER:
                    return
            elif in_port == 2:
                acts.append(psr.OFPActionOutput(3))
                if tproto.has_flags(tcp.TCP_SYN) and not tproto.has_flags(tcp.TCP_ACK):
                    self.ht[flow] = 1
                elif flow in self.ht:
                    self.ht[flow] += 1
                    if self.ht[flow] >= 10:
                        self.add_flow(dp, 1, match, acts, msg.buffer_id)
                        if msg.buffer_id != ofp.OFP_NO_BUFFER:
                            return
                else:
                    return
        #
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
