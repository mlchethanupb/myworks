import simpy 
import random


class Packet(object):
    def __init__(self, packet_size, start_time):     
        # track packet information
        self.id = random.randint(1, 1000)
        self.packet_size = packet_size  # unit?
        self.start_time = start_time
        self.hops = 0

    def update_statistics(self):
        self.hops += 1

    def __repr__(self):
        return str(self.id)