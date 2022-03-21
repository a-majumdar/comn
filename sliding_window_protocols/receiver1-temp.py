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
    received = sock.recvfrom(packet_length)

    while received: # while there is data in the socket, keep recieving it
        buffer = received[0]#receive data into buffer
        buffer = bytearray(buffer)#cast data into byte array

        eof = buffer[2]
        payload = buffer[3:]

        if eof == 1:
            print("End of file reached")
            f.write(payload)
            f.close()
            break

        f.write(payload)

        #receive next payload
        received = sock.recvfrom(packet_length)

    sock.close()


if __name__ == "__main__":
    main(sys.argv)
