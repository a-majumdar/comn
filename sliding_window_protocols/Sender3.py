import socket
import sys
import time
import select

payload_length = 1024
header_length = 3
ack_length = 2

def main(args):
    global address
    address = args[1]
    global port
    port = int(args[2])
    filename = args[3].encode('utf-8')
    global timeout
    timeout = int(args[4])
    window = int(args[5])

    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    f = open(filename, 'rb')

    time[0] = time.perf_counter()
    base = 0
    top = window - 1
    acked = 0
    queue = []

    # initialising queue
    for i in range(window):
        payload = f.read(payload_length)
        packet = bytearray()
        packet[0:0] = i.to_bytes(2, byteorder='big')
        packet[2:2] = (0).to_bytes(1, byteorder='big')
        packet[3:3] = bytearray(payload)
        queue.append(packet)

    while True:
        continue



if __name__ == "__main__":
    main(sys.argv)
