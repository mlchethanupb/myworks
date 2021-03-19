import random


class Updated_Routing_info(object):
    def __init__(self, dest, nh, hc, id_num):
        self.dest = dest
        self.nh = nh
        self.hc = hc
        self.id_num = id_num

    def update_destinations(self):
        return self.dest

    def update_next_hops(self):
        return self.nh

    def update_hop_counts(self):
        return self.hc

    def update_id(self):
        return self.id_num
