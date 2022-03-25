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
    received, address = sock.recvfrom(packet_length)
    print('Received first packet')

    while received: # while there is data in the socket, keep recieving it
        buffer = received[0]#receive data into buffer
        buffer = bytearray(buffer)#cast data into byte array
        seq_temp = 0

        seq = buffer[0:2] # sequence number
        eof = buffer[2]
        payload = buffer[3:]

        seq = int.from_bytes(seq, byteorder="big")

        if (seq == seq_temp + 1):
            seq_temp = seq
            packet = bytearray(seq.to_bytes(2, byteorder='big'))
            sock.sendto(packet, address)
            print('ACK sent')
        else:
            continue

        if eof == 1:
            print("End of filename reached")
            f.write(payload)
            f.close()
            break

        f.write(payload)

        #receive next payload
        received = sock.recvfrom(packet_length)

    sock.close()




if __name__ == "__main__":
    main(sys.argv)
