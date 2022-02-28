import socket
import sys
import time
import select

payload_length = 1024
header_length = 3

def timer():
    start = round(time.time() * 1000)
    while True:
        yield round(time.time() * 1000) - start

def main(argv):

    # argument vector starts from 0 but that includes the name of the script running, so the arguments used here start from argv[1]
    receiver_address = argv[1]
    receiver_port = int(argv[2])
    filename = argv[3].encode('utf-8')
    retry_timeout = int(argv[4])

    # to track performance properties
    file_size = 0
    retry_count = 0


    #set up socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    f = open(filename, 'rb')
    read_buffer = f.read(payload_length)

    start = time.time()

    total = 0
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

        total += 1

        sock.sendto(buffer, (receiver_address, receiver_port))

        t = timer()

        flag = True
        while flag:
            ready = select.select([sock], timeout=0)
            if ready:
                read_buffer = ready[0].recvfrom(2)
                ack = read_buffer[0]
                if seq == ack:
                    break
                else:
                    continue
            else:
                duration = next(t)
                if (duration >= retry_timeout):
                    retry_count += 1
                    # total += 1
                    continue

        #remember to update read buffer and sequence number
        file_size += len(read_buffer)
        read_buffer = f.read(payload_length)
        i+=1


    time_taken = time.time() - start
    print("{} {}".format(retry_count, round((file_size/time_taken)/1000)))

    f.close()
    sock.close()


def rdt_send():
    pass

def rdt_rcv():
    pass

def corrupt():
    pass

def isACK():
    pass

def timeout():
    pass

def notcorrupt():
    pass


if __name__ == "__main__":
    main(sys.argv)
