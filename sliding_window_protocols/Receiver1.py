import socket
import sys

packet_length = 1027

def main(args):

    port = int(args[1])
    filename = args[2]

    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    skt.bind(("0.0.0.0", port))

    f = open(filename, 'wb+')
    packets = read_socket(skt, filename)
    for packet in packets:
        buffer = bytearray(packet)

        eof = buffer[2]
        payload = buffer[3:]

        if eof == 1:
            print("File received")
            f.write(payload)
            f.close()
            break

        f.write(payload)

    skt.close()

def read_socket(skt, filename):
    packet = skt.recvfrom(packet_length)
    while packet:
        yield packet
        packet = skt.recvfrom(packet_length)


if __name__ == "__main__":
    main(sys.argv)
