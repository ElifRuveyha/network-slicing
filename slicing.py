from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
import threading,time,subprocess


class Slicing(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Slicing, self).__init__(*args, **kwargs)

        self.interface_thread = threading.Thread(target=self.interface, args=())
        self.interface_thread.daemon = True
        self.interface_thread.start()

        self.slices = {
            0: "production", 1: "management", 2: "development"
        }


        #switch id : {"dest MAC adress of the host" : eth port of the switch it is connected}
        self.mac_to_port = {
                1:{"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 2, "00:00:00:00:00:03": 3,
                   "00:00:00:00:00:04": 3, "00:00:00:00:00:06": 3, "00:00:00:00:00:08": 3},
                2:{"00:00:00:00:00:03": 1, "00:00:00:00:00:04": 2, "00:00:00:00:00:02": 3,
                   "00:00:00:00:00:01": 3, "00:00:00:00:00:08": 5},
        	3:{"00:00:00:00:00:05": 1, "00:00:00:00:00:06": 2, "00:00:00:00:00:01": 3,
        	   "00:00:00:00:00:07": 4},
        	4:{"00:00:00:00:00:07": 1, "00:00:00:00:00:08": 2, "00:00:00:00:00:02": 3,
                   "00:00:00:00:00:01": 3, "00:00:00:00:00:03": 3, "00:00:00:00:00:04": 3,
                   "00:00:00:00:00:05": 4}
        }


        self.slice2_hosts = {
            "00:00:00:00:00:05","00:00:00:00:00:07"
        }

        #if in slice 2 and tcp or icmp
        self.slice2_tcp_icmp_switch_to_port = {
            3:{"00:00:00:00:00:07":3, "00:00:00:00:00:05":1},
            4:{"00:00:00:00:00:07":1, "00:00:00:00:00:05":3},
            2:{"00:00:00:00:00:07":5, "00:00:00:00:00:05":4}
        }

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        #get packet information
        msg = ev.msg
        datapath = msg.datapath #switch id
        ofproto = datapath.ofproto #represents the openflow protocol negotiated
        in_port = msg.match["in_port"]

        #extract the packet from the message
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src

        #get the switch id
        dpid = datapath.id

        if dpid in self.mac_to_port:
            if dst in self.mac_to_port[dpid]:
                if dst in self.slice2_hosts:
                    if pkt.get_protocol(udp.udp):
                        out_port = self.mac_to_port[dpid][dst]
                        match = datapath.ofproto_parser.OFPMatch(
                            in_port=in_port,
                            eth_dst=dst,
                            eth_type=ether_types.ETH_TYPE_IP,
                            ip_proto=0x11,  # udp
                            udp_dst=pkt.get_protocol(udp.udp).dst_port,
                        )
                        actions = [datapath.ofproto_parser.OFPActionSetQueue(2),datapath.ofproto_parser.OFPActionOutput(out_port)]

                        # add to flow table
                        self.add_flow(datapath, 65530, match, actions)

                        #then execute the same command that was added to the flow table
                        self._send_package(msg, datapath, in_port, actions)
                    elif pkt.get_protocol(tcp.tcp):
                        out_port = self.slice2_tcp_icmp_switch_to_port[dpid][dst]
                        match = datapath.ofproto_parser.OFPMatch(
                            in_port=in_port,
                            eth_dst=dst,
                            eth_src=src,
                            eth_type=ether_types.ETH_TYPE_IP,
                            ip_proto=0x06,  # tcp
                        )
                        actions = [datapath.ofproto_parser.OFPActionSetQueue(4),datapath.ofproto_parser.OFPActionOutput(out_port)]

                        # add to flow table
                        self.add_flow(datapath, 65520, match, actions)

                        #then execute the same command that was added to the flow table
                        self._send_package(msg, datapath, in_port, actions)
                    elif pkt.get_protocol(icmp.icmp):
                        out_port = self.slice2_tcp_icmp_switch_to_port[dpid][dst]
                        match = datapath.ofproto_parser.OFPMatch(
                            in_port=in_port,
                            eth_dst=dst,
                            eth_src=src,
                            eth_type=ether_types.ETH_TYPE_IP,
                            ip_proto=0x01,  # icmp
                        )
                        actions = [datapath.ofproto_parser.OFPActionSetQueue(2),datapath.ofproto_parser.OFPActionOutput(out_port)]
                        # add to flow table
                        self.add_flow(datapath, 65520, match, actions)

                        #then execute the same command that was added to the flow table
                        self._send_package(msg, datapath, in_port, actions)
                else:
                    out_port = self.mac_to_port[dpid][dst]
                    match = datapath.ofproto_parser.OFPMatch(eth_dst=dst)
                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                    # add to flow table
                    self.add_flow(datapath, 1, match, actions)

                    #then execute the same command that was added to the flow table
                    self._send_package(msg, datapath, in_port, actions)


    def interface(self):
        time.sleep(1)
        subprocess.run(['python3', 'slice_manager.py'])
