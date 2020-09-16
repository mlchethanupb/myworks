import random


class Packet(object):
    def __init__(self,src,dest,nxt_hop):     
        # track packet information
        self.id = random.randint(1, 999999)
        self.src = src
        self.dest = dest
        self.nxt_hop = nxt_hop
        self.hop_count = 0

    def update_nxt_hop(self,nxt_hop):
        self.nxt_hop = nxt_hop

    def update_hop_count(self):
        self.hop_count += 1

    def return_id(self):
        return str(self.id)