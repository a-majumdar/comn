import socket
import sys

packet_length = 1027

def main(args):
    global port
    port = int(args[1])

    filename = args[2]

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", port))

    f = open(filename, 'wb+')

    seq_temp = 0
    while True:
        received, address = s.recvfrom(packet_length)
        buffer = bytearray(received)

        seq = buffer[0:2] # sequence number
        eof = buffer[2]
        payload = buffer[3:]

        seq = int.from_bytes(seq, byteorder="big")

        if (seq == seq_temp):
            seq_temp += 1
            packet = buffer[0:2]
            s.sendto(packet, address)
            f.write(payload)
            print('ACK sent')
            if eof == 1:
                # print("End of file reached")
                f.close()
                break
        else:
            packet = bytearray((seq_temp - 1).to_bytes(2, byteorder='big'))
            s.sendto(packet, address)
            print('ACK resent')


    s.close()


if __name__ == "__main__":
    main(sys.argv)
