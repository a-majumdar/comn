import socket
import sys
import time

payload_length = 1024
header_length = 3
ack_length = 2
finished = False
base = 0

def send_queue():
    for x in range(window):
        s.sendto(queue[x], (address, port))
        seq = int.from_bytes(queue[x][0:2], 'big')
        print('Packet {} sent from queue'.format(seq))

def make_and_send_packet(seq, sending):
    payload = f.read(payload_length)
    packet = bytearray()
    packet[0:0] = seq.to_bytes(2, byteorder='big')
    if len(payload) < payload_length:
        packet[2:2] = (1).to_bytes(1, 'big')
        finished = True
    else:
        packet[2:2] = (0).to_bytes(1, 'big')
    packet[3:3] = bytearray(payload)

    if sending:
        s.sendto(packet, (address, port))
        print('Packet {} sent individually'.format(seq))

    return packet

def send_and_time():
    retries = 0
    seq = int.from_bytes(queue[0][0:2], 'big')
    flag = False

    while True:
        start = time.perf_counter() * 1000
        now = start
        send_queue()
        while now - start < timeout:
            try:
                ack = int.from_bytes(s.recv(ack_length), 'big')
                if ack == seq:
                    base += 1
                    seq = base
                    flag = True
                    print("ACK {} received".format(base))

                    top += 1
                    queue.append(make_and_send_packet(top, True))
                    queue.pop(0)
                elif ack > seq:
                    acked = int.from_bytes(ack, 'big')
                    increment = acked - base + 1
                    base += increment
                    seq = base
                    flag = True
                    print("ACK {} received".format(acked))

                    for i in range(increment):
                        queue.append(make_and_send_packet(top + i, True))
                        queue.pop(0)

                    top += increment
            except:
                pass
            finally:
                now = time.perf_counter() * 1000
        if flag:
            return retries, seq
        retries += 1

def main(args):
    global address
    address = args[1]
    global port
    port = int(args[2])
    filename = args[3].encode('utf-8')
    global timeout
    timeout = int(args[4])
    global window
    window = int(args[5])

    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(0)

    global f
    f = open(filename, 'rb')

    times = []
    times.append(time.perf_counter() * 1000)
    global top
    top = window - 1
    global queue
    queue = []

    for i in range(window):
        queue.append(make_and_send_packet(i, False))

    retries = 0
    while queue:
        attempts, seq = send_and_time()
        retries += attempts

    times.append(time.perf_counter() * 1000)
    f.close()
    s.close()

    packets = top + retries
    throughput = round((packets * 1027) / (times[1] - times[0]))
    print(throughput)


if __name__ == "__main__":
    main(sys.argv)
