import socket
import sys

packet_length = 1027

def main(args):
    global port
    port = int(args[1])

    filename = args[2]

    window_size = args[3]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", port))

    f = open(filename, 'wb+')
    flag = True
    seq_temp = -1
    while flag:
        received, address = s.recvfrom(packet_length)
        buffer = bytearray(received)

        seq = buffer[0:2] # sequence number
        eof = buffer[2]
        payload = buffer[3:]

        seq = int.from_bytes(seq, byteorder="big")
