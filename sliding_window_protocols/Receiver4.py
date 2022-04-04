import socket
import sys
import math
import common

packet_length = 1027

def update_queue_and_write(packet):
    seq = get_seq(packet)
    if seq < base:
        return

    index = seq - base
    window[index] = packet
    while window[0] != None:
        f.write(get_payload(window[0]))
        del window[0]
        window.append(None)
        base += 1


def main(args):
    global port
    port = int(args[1])

    filename = args[2]

    global window
    window = int(args[3])

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", port))

    global f
    f = open(filename, 'wb+')

    global EOF
    EOF = math.inf
    global base
    base = 0
    global queue
    queue = [None] * window

    while True:
        packet, address = s.recvfrom(packet_length)
        seq = get_seq(packet)
        if seq >= base - window:
            sendACK(seq, s, address)

        update_queue_and_write(packet)
        if isEOF(packet):
            EOF = seq

        if base == EOF + 1:
            break

    s.settimeout(1)
    while True:
        try:
            packet, address = s.recvfrom(packet_length)
            sendACK(get_seq(packet), s, address)
        except timeout:
            break

    f.close()
    s.close()


if __name__ == "__main__":
    main(sys.argv)
