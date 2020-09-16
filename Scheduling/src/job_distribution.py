import numpy as np
import parameters
import random

class Dist:

    def __init__(self, num_resources, max_nw_size, job_len,job_small_chance):
        self.num_resources = num_resources
        self.max_nw_size = max_nw_size
        self.job_len = job_len

        self.job_small_chance = job_small_chance

        self.job_len_big_lower = job_len * 2 / 3
        self.job_len_big_upper = job_len

        self.job_len_small_lower = 1
        self.job_len_small_upper = job_len / 5

        self.dominant_res_lower = 0.25 * max_nw_size
        self.dominant_res_upper = 0.5 * max_nw_size

        self.other_res_lower = max(0.05 * max_nw_size, 1)
        self.other_res_upper = 0.1 * max_nw_size

    def normal_dist(self):

        # new work duration
        nw_len = np.random.randint(1, self.job_len + 1)  # same length in every dimension

        nw_size = np.zeros(self.num_resources)

        for i in range(self.num_resources):
            nw_size[i] = np.random.randint(1, self.max_nw_size + 1)

        return nw_len, nw_size

    def bi_model_dist(self,pa):

        # -- job length --
        if np.random.rand() < self.job_small_chance:  # small job
            nw_len = np.random.randint(self.job_len_small_lower,
                                       self.job_len_small_upper + 1)
        else:  # big job
            nw_len = np.random.randint(self.job_len_big_lower,
                                       self.job_len_big_upper + 1)

        nw_size = np.zeros(self.num_resources)

        # -- job resource request --
        dominant_res = pa.dominant_res # 0 and 1 for respecive indixes and 2 for both resources
        if dominant_res == 3:
            dominant_res = random.randint(0, 1)
            
        for i in range(self.num_resources):
            if i == dominant_res or dominant_res == 2:
                nw_size[i] = np.random.randint(self.dominant_res_lower,
                                               self.dominant_res_upper + 1)
            else:
                nw_size[i] = np.random.randint(self.other_res_lower,
                                               self.other_res_upper + 1)
        return nw_len, nw_size


def generate_sequence_work(pa):

    np.random.seed(pa.random_seed)

    simu_len = pa.simu_len * pa.num_ex

    nw_dist = pa.dist.bi_model_dist

    nw_len_seq = np.zeros(simu_len, dtype=int)
    nw_size_seq = np.zeros((simu_len, pa.num_resources), dtype=int)
    
    for i in range(simu_len):

        if np.random.rand() < pa.new_job_rate:  # a new job comes

            nw_len_seq[i], nw_size_seq[i, :] = nw_dist(pa)

    nw_size_seq_list = []
    for i in range(len(nw_size_seq)):
        nw_size_seq_list.append(list(nw_size_seq[i]))

    return list(nw_len_seq), nw_size_seq_list