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
        self.ht = set()

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
        # Define the internal host and external host port numbers
        INTERNAL_PORT_NUM = 1
        EXTERNAL_PORT_NUM = 2
        
        # Get the TCP and IP header information
        tcp_header = pkt.get_protocols(tcp.tcp)[0] if len(pkt.get_protocols(tcp.tcp)) != 0 else None
        ip_header = pkt.get_protocols(ipv4.ipv4)[0] if len(pkt.get_protocols(ipv4.ipv4)) != 0 else None

        # Define the default values for the flag and output port
        add_flow_flag = False
        out_port = ofp.OFPPC_NO_FWD

        # If the packet's tcp and ip headers are not empty then
        if tcp_header is not None and ip_header is not None:
            # If the input port is internal then 
            if in_port == INTERNAL_PORT_NUM:
                # If none of the illegal flag combinations are set then
                if tcp_header.has_flags(tcp.TCP_SYN) and not tcp_header.has_flags(tcp.TCP_FIN) and not tcp_header.has_flags(tcp.TCP_RST):
                    # Set the flag to add a flow
                    add_flow_flag = True
                    # Set the output port to the external host.
                    out_port = EXTERNAL_PORT_NUM
                    # Add the hash table to allow further activity on this TCP connection.
                    self.ht.add((ip_header.src, ip_header.dst, tcp_header.src_port, tcp_header.dst_port))

            # else if the input port is the external host then
            elif in_port == EXTERNAL_PORT_NUM:
                # If the reversed routing information is in the hash table then
                if (ip_header.dst, ip_header.src, tcp_header.dst_port, tcp_header.src_port) in self.ht:
                    # Set the flag to add a flow
                    add_flow_flag = True
                    # Set the output port to the internal host.
                    out_port = INTERNAL_PORT_NUM

        # Else the packet is not TCP-over-IPv4 so we can allow it to pass over the switch
        elif in_port == INTERNAL_PORT_NUM:
            out_port = EXTERNAL_PORT_NUM
        else: 
            out_port = INTERNAL_PORT_NUM
            
        # Create an action to the output port
        acts = [psr.OFPActionOutput(out_port)]

        # If we need to add a flow then
        if add_flow_flag:
            # Create a match rule for the TCP connection
            mtc = psr.OFPMatch(in_port=in_port, ip_proto=ip_header.proto, ipv4_src=ip_header.src, ipv4_dst=ip_header.dst, eth_type=eth.ethertype, tcp_src=tcp_header.src_port, tcp_dst=tcp_header.dst_port)
            # Add the flow rule
            self.add_flow(dp, 1, mtc, acts, msg.buffer_id)
            # If the packet has been buffered then return nothing
            if msg.buffer_id != ofp.OFP_NO_BUFFER:
                return
            
        #
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
