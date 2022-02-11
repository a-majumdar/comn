from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
from ipaddress import ip_address, ip_network
import sys
import matplotlib.pyplot as plt

class Node(object):
    def __init__(self, ip, plen):
        self.bytes = plen
        self.left = None
        self.right = None
        self.ip = ip
        
        
    def add(self, ip, plen):
        """ Function to recursively traverses the tree down to a leaf, then inserts a new entry with the given address and packet length.
        Args:
            ip (String): an ipv4 address.
            plen (float): the packet length.
        """
        # If the ip address is equal to current node then
        if ip == self.ip:
            # Add the packet length to the bytes of the current node.
            self.bytes += plen
        # If the ip address is less than the current node's ip address then.
        elif ip < self.ip:
            # If the there is not a left child node then.
            if self.left is None:
                # Create a new left child node with the ip address and packet length.
                self.left = Node(ip, plen)
            # Else call the add function of the left child.
            else:
                self.left.add(ip, plen)
        # Else the ip address will be greater than the current node's ip address
        else:
            # If the there is not a right child node then.
            if self.right is None:
                # Create a new right child node with the ip address and packet length.
                self.right = Node(ip, plen)
            # Else call the add function of the right child.
            else:
                self.right.add(ip, plen)
                
                
    def data(self, data):
        if self.left:
            self.left.data(data)
        if self.bytes > 0:
            data[ip_network(self.ip)] = self.bytes
        if self.right:
            self.right.data(data)
            
            
    @staticmethod 
    def supernet(ip1, ip2):
        """ Function which computes and returns the common network address and mask.
        Args:
            ip1 (String): an ip address which is either an IPv4Address or IPv4Network object.
            ip2 (String): an ip address which is either an IPv4Address or IPv4Network object.
        Returns:
            String: [description]
        """
        # Find the network addresses of the ip addresses
        na1 = ip_network(ip1).network_address
        na2 = ip_network(ip2).network_address
        # Calculate the number of bits that are the same starting from the lhs of the string.
        prefixlen = 32-(int(na1)^int(na2)).bit_length()
        # Find the binary string respsentation of the network address of one of the network addresses.
        na_binary = ''.join(["{0:08b}".format(int(x)) for x in str(na2).split('.')])
        # Find the address of the supernet by only keeping the first prefixlen number of bits.
        supernet_address = ip_address(int(na_binary[:prefixlen].ljust(32, '0'), 2))
        # Format the ip address correctly with its prefix length.
        return ip_network("{}/{}".format(supernet_address, prefixlen), strict=False)
    
    
    def aggr(self, byte_thresh):
        """ Function to recursively aggregate nodes which have less than the threshold traffic.
        Args:
            byte_thresh (float): number of bytes to be aggregated.
        """
        # If the current node has a left node then            
        if self.left is not None:
            # Call the aggregate function on the left node
            self.left.aggr(byte_thresh)
            # If the number of bytes in the left node is less than the threshold
            if self.left.bytes < byte_thresh:
                # Add the bytes of the left node to the current node
                self.bytes += self.left.bytes
                # Set the number of bytes on the left node to 0
                self.left.bytes = 0
                # Calculate the supernet address of the current node's ip address and the left node ip.
                self.ip = self.supernet(self.ip, self.left.ip)
                # If the left node is a leaf node (it has no left or right nodes itself) then
                if self.left.left is None and self.left.right is None:
                    # Delete the left node.
                    self.left = None
        # If the current node has a right node then     
        if self.right is not None:
            # If the node has a right node then
            self.right.aggr(byte_thresh)
            # If the number of bytes in the right node is less than the threshold
            if self.right.bytes < byte_thresh:
                # Add the bytes of the right node to the current node
                self.bytes += self.right.bytes
                # Set the number of bytes on the right node to 0
                self.right.bytes = 0
                # Calculate the supernet address of the current node's ip address and the right node ip.
                self.ip = self.supernet(self.ip, self.right.ip)
                # If the right node is a leaf node (it has no left or right nodes itself) then
                if self.right.left is None and self.right.right is None:
                    # Delete the right node.
                    self.right = None
            
            
class Data(object):
    def __init__(self, data):
        self.tot_bytes = 0
        self.data = {}
        self.aggr_ratio = 0.05
        root = None
        cnt = 0
        for pkt, metadata in RawPcapReader(data):
            ether = Ether(pkt)
            if not 'type' in ether.fields:
                continue
            if ether.type != 0x0800:
                continue
            ip = ether[IP]
            self.tot_bytes += ip.len
            if root is None:
                root = Node(ip_address(ip.src), ip.len)
            else:
                root.add(ip_address(ip.src), ip.len)
            cnt += 1
        root.aggr(self.tot_bytes * self.aggr_ratio)
        root.data(self.data)
        
        
    def Plot(self):
        data = {k: v/1000 for k, v in self.data.items()}
        plt.rcParams['font.size'] = 8
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(which='major', axis='y')
        ax.tick_params(axis='both', which='major')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels([str(l) for l in data.keys()], rotation=45,
            rotation_mode='default', horizontalalignment='right')
        ax.set_ylabel('Total bytes [KB]')
        ax.bar(ax.get_xticks(), data.values(), zorder=2)
        ax.set_title('IPv4 sources sending {} % ({}KB) or more traffic.'.format(
            self.aggr_ratio * 100, self.tot_bytes * self.aggr_ratio / 1000))
        plt.savefig(sys.argv[1] + '.aggr.pdf', bbox_inches='tight')
        plt.close()
        
        
    def _Dump(self):
        with open(sys.argv[1] + '.aggr.data', 'w') as f:
            f.write('{}'.format({str(k): v for k, v in self.data.items()}))


if __name__ == '__main__':
    d = Data(sys.argv[1])
    d.Plot()
    d._Dump()