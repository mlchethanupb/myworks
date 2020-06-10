import simpy 
import random


class Packet(object):
    def __init__(self, start_time):     
        # track packet information
        self.id = random.randint(1, 999999)
        self.start_time = start_time
        self.hopcount = 0

    def update_statistics(self):
        self.hopcount += 1

    def __repr__(self):
        return str(self.id)