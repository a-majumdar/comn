import socket
import sys
import time
import select

payload_length = 1024
header_length = 3
ack_length = 2

## TODO:
# 1. set up socket
# 2. open file for transfer
# 3. send packet, start timer
# 4. if timeout, resend packet
# 5. once ACK received, prepare next packet
# 6. repeat 3-5 until whole file is transferred

def timer():
    start = round(time.perf_counter() * 1000)
    while True:
        yield round(time.perf_counter() * 1000) - start

def send_packet(packet, seq):
    retries = 0
    while True:
        s.sendto(packet, (address, port))
        t = timer()
        while (next(t) < timeout):
            ack = s.recvfrom(2)
            if (ack and int.from_bytes(ack, byteorder='big') == seq):
                return retries
        retries += 1


def main(argv):
    # performance trackers
    packets = 0
    retries = 0

    # intitialising
    global address
    address = argv[1]
    global port
    port = int(argv[2])
    filename = argv[3].encode('utf-8')
    global timeout
    timeout = int(argv[4])

    # 1. set up socket
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 2. open file for transfer
    f = open(filename, 'rb')

    # 3a. starting loop
    start = time.perf_counter() * 1000
    seq = 0
    flag = True
    while flag:
        # 3b. making packet
        payload = f.read(payload_length)

        if (len(payload) < payload_length):
            eof = (1).to_bytes(1, byteorder='big')
            flag = False
        else:
            eof = (0).to_bytes(1, byteorder='big')

        packet = bytearray()
        packet[0:0] = seq.to_bytes(2, byteorder='big')
        packet[2:2] = eof
        packet[3:3] = bytearray(payload)

        # 3. send packet, start timer
        retries += send_packet(packet, seq)
        seq += 1

    time_taken = (time.perf_counter() * 1000) - start

    f.close()
    s.close()

    packets = seq + retries
    output = "{} {}".format(retries, round((packets*1024/time_taken)/1000))
    print(output)


if __name__ == "__main__":
    main(sys.argv)
