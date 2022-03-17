import socket
import sys

payload_length = 1024
header_length = 3
placeholder_max = 1000

def main(args):
    receiver_address = argv[1]
    receiver_port = int(argv[2])
    filename = argv[3].encode('utf-8')

    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    packets = read_buffer(skt, filename)
    counter = 0
    for packet in packets:
        sequence = counter.to_bytes(2, byteorder = 'big')
        if (len(packet) < payload_length):
            eof = (1).to_bytes(1, byteorder = 'big')
        else:
            eof = (0).to_bytes(1, byteorder = 'big')

        header = bytearray(sequence)
        header += bytearray(eof)
        payload = bytearray(packet)
        to_send = header + payload


def read_buffer(skt, filename):
    f = open(filename, 'rb')
    packet = f.read(payload_length)
    while packet:
        yield packet
        packet = f.read(payload_length)

if __name__ == "__main__":
    main(sys.argv)
