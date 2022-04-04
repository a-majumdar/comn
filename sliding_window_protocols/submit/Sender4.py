/* Ananya Majumdar 1802817 */

import sys
import math
import time
import socket
import common
import threading

payload_length = 1024
header_length = 3
ack_length = 2

def next_packet():
    payload = f.read(payload_length)
    file += len(packet)
    if len(payload) < payload_length:
        return create_packet(payload, nextSeq, True)
    else:
        return create_packet(payload, nextSeq, False)

def update_queue(ack):
    if ack < base:
        return
    index = ack - base
    acks[index] = True
    while acks[0] == True:
        del queue[0]
        queue.append(None)
        del acks[0]
        acks.append(False)
        base += 1

def send():
    while True:
        lock.acquire()
        while nextSeq < base + window:
            packet = next_packet()
            if nextSeq == 0:
                start = time.perf_counter()

            index = nextSeq - base
            queue[index] = packet
            s.sendto(packet, (address, port))

            timer = threading.Timer(timeout, timeout, args = (nextSeq, ))
            timer.start()

            nextSeq += 1

            if isEOF(packet):
                EOFSeq = get_seq(packet)
                lock.release()
                return

        lock.release()
        time.sleep(0.01)

def receive():
    while True:
        ack, _ = s.recvfrom(ack_length)
        lock.acquire()
        ack = int.from_bytes(ack, 'big')
        update_queue(ack)

        if base > EOFSeq:
            throughput = (file / 1024) / (time.perf_counter() - start)
            lock.release()
            return

        lock.release()

def timeout(seq):
    lock.acquire()
    if base > seq or acks[seq - base]:
        lock.release()
        return

    s.sendto(queue[seq - base], (address, port))
    timer = threading.Timer(timeout, timeout, args = (seq, ))
    timer.start()
    lock.release()


def main(args):
    global address
    address = args[1]
    global port
    port = int(args[2])
    filename = args[3].encode('utf-8')
    global timeout
    timeout = int(args[4]) / 1000
    global window
    window = int(args[5])

    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout / 1000)

    global f
    f = open(filename, 'rb')

    global base
    base = 0
    global nextSeq
    nextSeq = 0
    global EOFSeq
    EOFSeq = math.inf
    global queue
    queue = [None] * window
    global acks
    acks = [False] * window
    lock = threading.Lock()

    global start
    start = 0
    global file
    file = 0
    global throughput
    throughput = 0

    sender = threading.Thread(target = send)
    receiver = threading.Thread(target = receive)

    sender.start()
    receiver.start()

    sender.join()
    receiver.start()

    print(throughput)
    f.close()
    s.close()

if __name__ == "__main__":
    main(sys.argv)
