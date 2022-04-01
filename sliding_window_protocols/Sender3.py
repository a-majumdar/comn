import socket
import sys
import time
import select

payload_length = 1024
header_length = 3
ack_length = 2

def send_queue():
    for x in range(len(queue)):
        s.sendto(queue[x], (address, port))

def send_and_time():
    retries = 0
    seq = queue[0][0:2]
    while True:
        start = time.perf_counter() * 1000
        now = start
        send_queue()
        while now - start < timeout:
            try:
                ack = s.recv(ack_length)
                if ack == seq:
                    return retries
                now = time.perf_counter() * 1000
            except:
                now = time.perf_counter() * 1000
        retries += 1

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
    s.setblocking(0)

    f = open(filename, 'rb')

    times = []
    times.append(time.perf_counter() * 1000)
    base = 0
    top = window - 1
    acked = 0
    global queue
    queue = []

    # initialising queue
    for i in range(window):
        payload = f.read(payload_length)
        packet = bytearray()
        packet[0:0] = i.to_bytes(2, byteorder='big')
        packet[2:2] = (0).to_bytes(1, byteorder='big')
        packet[3:3] = bytearray(payload)
        queue.append(packet)

    retries = 0
    finished = False
    while queue:
        retries += send_and_time()
        top += 1
        if not finished:
            payload = f.read(payload_length)
            packet = bytearray()
            packet[0:0] = top.to_bytes(2, 'big')
            if len(payload) < payload_length:
                packet[2:2] = (1).to_bytes(1, 'big')
                finished = True
            else:
                packet[2:2] = (0).to_bytes(1, 'big')
            packet[3:3] = bytearray(payload)
            queue.append(packet)

        queue.pop(0)

    times.append(time.perf_counter() * 1000)
    f.close()
    s.close()

    packets = top + retries
    throughput = round((packets * 1027) / (times[1] - times[0]))
    print(throughput)


if __name__ == "__main__":
    main(sys.argv)
