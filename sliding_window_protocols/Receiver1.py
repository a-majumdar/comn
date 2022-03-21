import socket
import sys

packet_length = 1027

def main(args):

    port = int(args[1])
    filename = args[2]


    f = open(filename, 'wb+')
    packets = read_socket(port)
    for packet in packets:
        # buffer = bytearray(packet)

        eof = packet[2]
        payload = packet[3:]

        if eof == 1:
            print("File received")
            f.write(payload)
            f.close()
            break

        f.write(payload)


def read_socket(port):
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    skt.bind(("0.0.0.0", port))
    packet = skt.recvfrom(packet_length)
    while packet:
        print(packet)
        yield packet
        packet = skt.recvfrom(packet_length)
    skt.close()


if __name__ == "__main__":
    main(sys.argv)
