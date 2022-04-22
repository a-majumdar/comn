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

class L4State14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4State14, self).__init__(*args, **kwargs)
        self.ht = set() # sequence of distinct iterable elements

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
        #
        # write your code here
        other_port = [1, 2].remove(in_port)
        # forwarding = True
        if pkt.get_protocol(tcp.tcp) and pkt.get_protocol(ipv4.ipv4):
        #     forwarding = False
        # if not forwarding:
            smac, dmac = (eth.src, eth.dst)
            tproto = pkt.get_protocol(tcp.tcp)
            nproto = pkt.get_protocol(ipv4.ipv4)
            sip, dip = (nproto.src, nproto.dst)
            sport, dport = (tproto.src_port, tproto.dst_port)
            flow = (in_port, sip, dip, sport, dport)
            match = psr.OFPMatch(in_port=in_port, ipv4_src=sip, ipv4_dst=dip, tcp_src=sport, tcp_dst=dport)
            acts = [psr.OFPActionOutput(other_port)]
            if in_port == 1:
                flagged = tproto.has_flags(tcp.TCP_SYN) or tproto.has_flags(tcp.TCP_FIN) or tproto.has_flags(tcp.TCP_RST)
                synfin = tproto.has_flags(tcp.TCP_SYN) and tproto.has_flags(tcp.TCP_FIN)
                synrst = tproto.has_flags(tcp.TCP_SYN) and tproto.has_flags(tcp.TCP_RST)
                if flagged and not (synfin or synrst):
                    acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]
                    if not (flow in self.ht):
                        self.add_flow(dp, 1, match, acts, msg.buffer_id)
                        self.ht.add(flow)
            else:
                if (other_port, dip, sip, dport, sport) in self.ht:
                    self.add_flow(dp, 1, match, acts, msg.buffer_id)
                    self.ht.add(flow)
                else:
                    acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]
        else:
            acts = [psr.OFPActionOutput(other_port)]
        #
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
