import job_distribution
from stable_baselines import A2C,PPO2

class Parameters:
    #intializing parameters required for env
    def __init__(self):

        self.simu_len = 60
        # length of the busy cycle that repeats itself
        self.num_ex = 1
        # number of sequences
        self.output_freq = 10
        # interval for output and store parameters
        self.num_seq_per_batch = 10
        # number of sequences to compute baseline ???
        self.episode_max_length = self.simu_len * self.simu_len * 20
        # enforcing an artificial terminal - no of feasable training episodes
        self.num_resources = 2
        # number of resources in the system - CPU,Memory
        self.job_wait_queue = 5
        # maximum allowed number of work/jobs in the queue. M
        self.time_horizon = 20
        # number of time steps in the graph
        self.max_job_len = self.time_horizon * 0.75         
        # maximum duration of new jobs
        self.res_slot = 10             
        # maximum number of available resource slots
        self.max_job_size = self.res_slot         
        # maximum resource request of new work/Jobs
        self.backlog_size = 60
        # backlog queue size in waiting queue to go in M.
        self.max_track_since_new = 10
        # track how many time steps since last new jobs
        self.job_num_cap = 40
        # maximum number of distinct colors in current work graph . not required
        self.new_job_rate = 1.3 
        assert self.backlog_size % self.time_horizon == 0
        # penalty for delaying things in the current work screen
        self.penalty = -1 
        # supervised learning mimic policy
        self.batch_size = 10
        # random number seed
        self.random_seed = 42
        self.num_episode = 10
        self.job_small_chance = 0.8
        # 0,1,3 for any one dominant and 2 for both dominant resources, 4,5, etc... for all other
        self.dominant_res = 3 
        self.dist = job_distribution.Dist(self.num_resources, self.max_job_size, self.max_job_len, self.job_small_chance)
        self.A2C_Ctime = {'agent':A2C, 'save_path':'job_scheduling_A2C_Ctime', 'log_dir':"/home/aicon/aluri/workspace/tensor_A2C_Ctime/",'color':'Red', 'title':'A2C Ctime agent', 'figure_name':'learning_curve_Ctime.png'}
        self.A2C_Slowdown = {'agent':A2C, 'save_path':'job_scheduling_A2C_Slowdown', 'log_dir':"/home/aicon/aluri/workspace/tensor_A2C_Slowdown/", 'color':'Blue', 'title':'A2C Slowdown agent', 'figure_name':'learning_curve_Slowdown.png'}
        self.PPO2 = {'agent':PPO2, 'save_path':'job_scheduling_PPO2', 'log_dir':"/home/aicon/aluri/workspace/tensor_PPO2/", 'color':'Green', 'title':'PPO2 agent', 'figure_name':'learning_curve_PPO2.png'}
        self.random = {'agent':None, 'save_path':None,'color':'Yellow', 'title':'Random agent', 'figure_name':'learning_curve_Random.png'}
        self.objective = self.A2C_Slowdown