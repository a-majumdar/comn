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

    start = time.perf_counter()
    seq = 0
