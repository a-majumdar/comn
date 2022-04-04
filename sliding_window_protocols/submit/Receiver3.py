/* Ananya Majumdar 1802817 */

import sys
import socket
import common

packet_length = 1027

def main(args):
    global port
    port = int(args[1])

    filename = args[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", port))

    global f
    f = open(filename, 'wb+')

    global expected
    expected = 1

    while True:
        packet, address = s.recvfrom(packet_length)
        seq = get_seq(packet)
        if expected == seq:
            file.write(get_payload(packet))
            expected += 1

        sendACK(expected - 1, s, address)
        if isEOF(packet) and seq == expected - 1:
            break

    s.settimeout(1)
    while True:
        try:
            packet, address = s.recvfrom(packet_length)
            sendACK(expected - 1, s, address)
        except timeout:
            break

    s.close()


if __name__ == "__main__":
    main(sys.argv)
