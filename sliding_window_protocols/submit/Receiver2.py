/* Ananya Majumdar 1802817 */

import socket
import sys

packet_length = 1027

def main(args):

    port = int(args[1])
    filename = args[2]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))


    #open filename for writing to
    f = open(filename, 'wb+')

    seq_temp = 0
    while True: # while there is data in the socket, keep recieving it
        # print('getting packet')
        received, address = sock.recvfrom(packet_length)
        buffer = bytearray(received)

        seq = buffer[0:2] # sequence number
        eof = buffer[2]
        payload = buffer[3:]

        seq = int.from_bytes(seq, byteorder="big")

        if (seq == seq_temp):
            seq_temp += 1
            packet = buffer[0:2]
            sock.sendto(packet, address)
            f.write(payload)
            # print('ACK sent')
            if eof == 1:
                # print("End of filename reached")
                f.close()
                break
        else:
            packet = bytearray(seq.to_bytes(2, byteorder='big'))
            sock.sendto(packet, address)
            # print('ACK resent')


    sock.close()


if __name__ == "__main__":
    main(sys.argv)
