import socket
import sys

payload_length = 1024
header_length = 3
placeholder_max = 1000

def main(argv):
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

        skt.sendto(to_send, (receiver_address, receiver_port))

        counter += 1

    skt.close()



def read_buffer(skt, filename):
    f = open(filename, 'rb')
    packet = f.read(payload_length)
    while packet:
        yield packet
        packet = f.read(payload_length)
    f.close()

if __name__ == "__main__":
    main(sys.argv)
