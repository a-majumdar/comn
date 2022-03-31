import socket
import sys

packet_length = 1027

def main(args):
    global port
    port = int(args[1])

    filename = args[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    f = open(filename, 'wb+')

    
