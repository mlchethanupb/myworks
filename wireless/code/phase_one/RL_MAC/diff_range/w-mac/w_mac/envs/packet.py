import random


class Packet(object):
    def __init__(self,src,dest,nxt_hop):     
        # track packet information
        self.id = random.randint(1, 999999)
        self.next_hop = 0
        self.src = src
        self.dest = dest
        self.nxt_hop = nxt_hop

    def update_nxt_hop(self,nxt_hop):
        self.nxt_hop = nxt_hop

    def return_id(self):
        return str(self.id)