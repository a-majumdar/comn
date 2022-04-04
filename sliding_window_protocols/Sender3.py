import socket
import sys
import time
import math
import threading
import common

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

def send_queue():
    for packet in window:
        s.sendto(packet, (address, port))

def update_queue(ack):
    increment = ack - base + 1
    del queue[:increment]
    base = ack + 1


def send():
    global nextSeq
    nextSeq = 1
    global EOFSeq
    EOFSeq = math.inf
    while not lastACKed:
        lock.acquire()
        while nextSeq < base + window and EOFSeq == math.inf:
            packet = next_packet()
            if nextSeq == 1:
                start = time.perf_counter()
            queue.append(packet)
            s.sendto(packet, (address, port))

            if base == nextSeq:
                timer.start()

            nextSeq += 1

            if isEOF(packet):
                EOFSeq = get_seq(packet)

        lock.release()
        time.sleep(0.01)


def receive():
    global lastACKed
    lastACKed = False
    while not lastACKed:
        ack, _ = s.recvfrom(ack_length)
        lock.acquire()
        ack = int.from_bytes(ack, 'big')
        if ack < base:
            lock.release()
            continue

        update_queue()
        if base == nextSeq:
            timer.stop()
        else:
            timer.start()

        if ack == EOFSeq:
            lastACKed = True
            throughput = (file / 1024) / (time.perf_counter() - start)

        lock.release()

def timeout():
    while not lastACKed:
        lock.acquire()
        if timer.timed_out():
            timer.start()
            send_queue()
            sleep = timeout
        elif timer.running():
            sleep = max(0.001, timer.start + timeout - time.perf_counter())
        else:
            sleep = timeout

        lock.release()
        time.sleep(sleep)


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

    global timer
    timer = common.Timer(timeout)

    global base
    base = 1
    global queue
    queue = []
    global lock
    lock = threading.Lock()

    global start
    start = 0
    global file
    file = 0
    global throughput
    throughput = 0

    s.setblocking(1)

    sender = threading.Thread(target = send)
    receiver = threading.Thread(target = receive)
    timeouts = threading.Thread(target = timeout)

    sender.start()
    receiver.start()
    timeouts.start()

    sender.join()
    receiver.join()
    timeouts.join()

    print(throughput)
    f.close()
    s.close()


if __name__ == "__main__":
    main(sys.argv)
