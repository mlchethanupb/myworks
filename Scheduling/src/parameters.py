class Parameters:
    #intializing parameters required for env
    def __init__(self):

        self.simu_len = 10
        # length of the busy cycle that repeats itself
        self.num_ex = 1
        # number of sequences
        self.output_freq = 10
        # interval for output and store parameters
        self.num_seq_per_batch = 10
        # number of sequences to compute baseline ???
        self.episode_max_length = 200
        # enforcing an artificial terminal - no of feasable training episodes
        self.num_resources = 2
        # number of resources in the system - CPU,Memory
        self.job_wait_queue = 5
        # maximum allowed number of work/jobs in the queue. M
        self.time_horizon = 20
        # number of time steps in the graph
        self.max_job_len = 15          
        # maximum duration of new jobs
        self.res_slot = 10             
        # maximum number of available resource slots
        self.max_job_size = 10         
        # maximum resource request of new work/Jobs
        self.backlog_size = 60
        # backlog queue size in waiting queue to go in M.
        self.max_track_since_new = 10
        # track how many time steps since last new jobs
        self.job_num_cap = 40
        # maximum number of distinct colors in current work graph . not required
        self.new_job_rate = 0.7
        assert self.backlog_size % self.time_horizon == 0
        self.penalty = -1       # penalty for delaying things in the current work screen
        # supervised learning mimic policy
        self.batch_size = 10
