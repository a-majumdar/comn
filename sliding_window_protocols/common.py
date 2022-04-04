import time
import math

def isEOF(packet):
    return int.from_bytes(packet[2], 'big') == 1

def get_payload(packet):
    return packet[3:]

def get_seq(packet):
    return int.from_bytes(packet[0:2], 'big')

def sendACK(seq, s, address):
    ack = seq.to_bytes(2, 'big')
    s.sendto(ack, address)

def create_packet(payload, seq, eof):
    seq = seq.to_bytes(2, 'big')
    if eof:
        flag = (1).to_bytes(1, 'big')
    else:
        flag = (0).to_bytes(1, 'big')

    return b''.join([seq, flag, payload])


class Timer:
    def __init__(self, timeout):
        self.start = math.inf
        self.timeout = timeout

    def start(self):
        self.start = time.perf_counter()

    def stop(self):
        self.start = math.inf

    def timed_out(self):
        return time.perf_counter() > self.start + self.timeout

    def running(self):
        return self.start != math.inf
