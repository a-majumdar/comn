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
        pin = 1
        pout = 2

        iph = pkt.get_protocols(ipv4.ipv4)
        iph = iph[0] if len(iph) != 0 else None
        tcph = pkt.get_protocols(tcp.tcp)
        tcph = tcph[0] if len(tcph) != 0 else None

        acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]
        match = psr.OFPMatch()

        forwarding = False if (iph is not None and tcph is not None) else True
        if forwarding:
            other_port = pout if in_port == pin else pin
            acts = [psr.OFPActionOutput(other_port)]
        else:
            smac, dmac = (eth.src, eth.dst)
            sip, dip = (iph.src, iph.dst)
            sport, dport = (tcph.src_port, tcph.dst_port)
            flow = (sip, dip, sport, dport)
            match = psr.OFPMatch(in_port=in_port, ip_proto=iph.proto, ipv4_src=sip, ipv4_dst=dip, eth_type=eth.ethertype, tcp_src=sport, tcp_dst=dport)

            if in_port == pin:
                flagged = tcph.has_flags(tcp.TCP_SYN) or tcph.has_flags(tcp.TCP_FIN) or tcph.has_flags(tcp.TCP_RST)
                synfin = tcph.has_flags(tcp.TCP_SYN) and tcph.has_flags(tcp.TCP_FIN)
                synrst = tcph.has_flags(tcp.TCP_SYN) and tcph.has_flags(tcp.TCP_RST)
                if flagged and not (synfin or synrst):
                    acts = [psr.OFPActionOutput(pout)]
                    self.add_flow(dp, 1, match, acts, msg.buffer_id)
                    self.ht.add(flow)
                    print("Problem 1")
            else:
                if (dip, sip, dport, sport) in self.ht:
                    acts = [psr.OFPActionOutput(pin)]
                    self.add_flow(dp, 1, match, acts, msg.buffer_id)
                    self.ht.add(flow)
                    print("Problem 2")

        if msg.buffer_id != ofp.OFP_NO_BUFFER:
            return
        print("Passing if-else block")
        #
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
