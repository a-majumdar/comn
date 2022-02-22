import socket
import sys

payload_length = 1024
header_length = 3

def main(argv):

    receiver_address = argv[0]
    receiver_port = int(argv[1])
    filename = argv[2].encode('utf-8')

    #set up socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    f = open(filename, 'rb')
    read_buffer = f.read(payload_length)
    i = 0
    while (read_buffer):
        seq = i.to_bytes(2, byteorder='big')#first 2 bytes for sequence number
        eof = (0).to_bytes(1, byteorder='big')#3rd byte for EOF


        if (len(read_buffer) < payload_length):
            print("End of file reached")
            eof = (1).to_bytes(1, byteorder='big')

        buffer = bytearray()
        buffer[0:0] = seq
        buffer[2:2] = eof
        buffer[3:3] =  bytearray(read_buffer)
        sock.sendto(buffer, (receiver_address, receiver_port))

        #remember to update read buffer and sequence number
        read_buffer = f.read(payload_length)
        i+=1

    f.close()
    sock.close()


if __name__ == "__main__":
    main(sys.argv)
