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
        # Define the internal host and external host port numbers
        INTERNAL_PORT_NUM = 1
        EXTERNAL_PORT_NUM = 2
        MIRROR_PORT_NUM = 3

        # Get the TCP and IP header information
        tcp_header = tcph[0] if len(tcph) != 0 else None
        ip_header = iph[0] if len(iph) != 0 else None
        
        # Define the default values for the flag
        add_flow_flag = False
        
        # Create an action to the output port
        acts = [psr.OFPActionOutput(out_port)]
        
        # If the packet's tcp and ip headers are not empty then
        if tcp_header is not None and ip_header is not None:
            # If the input port is internal then 
            if in_port == INTERNAL_PORT_NUM:
                # Set the flag to add a flow
                add_flow_flag = True
            # Else if the input port is one of the other hosts
            elif in_port == EXTERNAL_PORT_NUM:
                # Create the address tuple of the packet
                address = (ip_header.src, ip_header.dst, tcp_header.src_port, tcp_header.dst_port)
                # If none of the illegal flag combinations are set then
                if tcp_header.has_flags(tcp.TCP_SYN) and not tcp_header.has_flags(tcp.TCP_FIN) and not tcp_header.has_flags(tcp.TCP_RST):
                    # Set the hash table value for the address to equal 1
                    self.ht[address] = 1
                    # Create two new actions to send to the internal port and duplicate to the other host
                    acts.append(psr.OFPActionOutput(MIRROR_PORT_NUM))
                # Else if the address is in the hash table then
                elif address in self.ht:
                    # Increment the hash table value for the address by 1
                    self.ht[address] = self.ht[address] + 1
                    # Create two new actions to send to the internal port and duplicate to the other host
                    acts.append(psr.OFPActionOutput(MIRROR_PORT_NUM))
                # Else return nothing
                else:
                    return
                # If the address is in the hash table and entry equals 10 then
                if address in self.ht and self.ht[address] >= 10:
                    # Remove the address from the hash table
                    self.ht.pop(address, None)
                    # Set the flag to add a flow
                    add_flow_flag = True
                    
        # If we need to add a flow then
        if add_flow_flag:
            # Create a match rule for the TCP connection
            mtc = psr.OFPMatch(in_port=in_port, ip_proto = ip_header.proto, ipv4_src=ip_header.src, ipv4_dst = ip_header.dst, eth_type=eth.ethertype, tcp_src=tcp_header.src_port, tcp_dst=tcp_header.dst_port)
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
