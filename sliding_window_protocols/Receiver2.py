import socket
import sys

packet_length = 1027

def main(args):

    port = int(args[1])
    filename = args[2]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))#bind to all interfaces


    #open filename for writing to
    f = open(filename, 'wb+')

    seq_temp = 0
    while True: # while there is data in the socket, keep recieving it
        print('getting next packet')
        received, address = sock.recv(packet_length)
        buffer = bytearray(received)#cast data into byte array

        seq = buffer[0:2] # sequence number
        eof = buffer[2]
        payload = buffer[3:]

        seq = int.from_bytes(seq, byteorder="big")

        if (seq == seq_temp):
            seq_temp += 1
            packet = bytearray(seq.to_bytes(2, byteorder='big'))
            sock.sendto(packet, address)
            print('ACK sent')
            if eof == 1:
                print("End of filename reached")
                f.write(payload)
                f.close()
                break

        else:
            packet = bytearray(seq_temp.to_bytes(2, byteorder='big'))
            sock.sendto(packet, address)
            print('ACK for last packet sent')
            continue


        f.write(payload)


    sock.close()




if __name__ == "__main__":
    main(sys.argv)
