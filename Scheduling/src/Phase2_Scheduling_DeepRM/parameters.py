# File for parameters.
import job_distribution
from stable_baselines import A2C, PPO2, DQN
import math


class Parameters:
    # intializing parameters required for env
    def __init__(self):

        self.simu_len = 100  # for complete 1.9 cluster load
        # length of the busy cycle that repeats itself
        self.num_ex = 100
        # number of sequences
        self.output_freq = 10
        # interval for output and store parameters
        self.num_seq_per_batch = 10
        # number of sequences to compute baseline ???
        self.episode_max_length = 2000
        # enforcing an artificial terminal - no of feasable training episodes
        self.num_res = 2
        # number of resources in the system - CPU,Memory
        self.num_nw = 5
        # maximum allowed number of work/jobs in the queue. M
        self.time_horizon = 20
        # number of time steps in the graph
        self.max_job_len = self.time_horizon * 0.75
        # maximum duration of new jobs
        self.res_slot = 20
        # maximum number of available resource slots
        self.max_job_size = 10
        # maximum resource request of new work/Jobs
        self.backlog_size = 60
        # backlog queue size in waiting queue to go in M.
        self.max_track_since_new = 10
        # track how many time steps since last new jobs
        self.job_num_cap = 40
        # maximum number of distinct colors in current work graph . not required
        self.new_job_rate = 1
        assert self.backlog_size % self.time_horizon == 0
        # penalty for delaying things in the current work screen
        self.penalty = -1
        # supervised learning mimic policy
        self.verbose = 1
        self.batch_size = 10
        # random number seed
        self.random_seed = 42
        self.num_episode = 10
        self.job_small_chance = 0.8
        self.cluster_capacity = (
            self.res_slot ** self.num_res) * self.time_horizon
        self.cluster_load = 1.3
        self.cluster_occupied = 0
        # 0,1,3 for any one dominant and 2 for both dominant resources, 4,5, etc... for all other
        self.dominant_res = 3
        self.check_freq = 10000
        self.training_time = 1e7
        # graphical representation
        # such that it can be converted into an image
        assert self.backlog_size % self.time_horizon == 0
        self.backlog_width = int(
            math.ceil(self.backlog_size / float(self.time_horizon)))
        self.network_input_height = self.time_horizon
        self.network_input_width = \
            (self.res_slot +
             self.max_job_size * self.num_nw) * self.num_res + \
            self.backlog_width + \
            1  # for extra info, 1) time since last new job

        # compact representation
        self.network_compact_dim = (self.num_res + 1) * \
            (self.time_horizon + self.num_nw) + 1  # + 1 for backlog indicator

        self.network_output_dim = self.num_nw + 1  # + 1 for void action

        self.delay_penalty = -1       # penalty for delaying things in the current work screen
        self.hold_penalty = -1        # penalty for holding things in the new work screen
        self.dismiss_penalty = -1     # penalty for missing a job because the queue is full

        self.num_frames = 1           # number of frames to combine and process
        self.lr_rate = 0.001          # learning rate
        self.rms_rho = 0.9            # for rms prop
        self.rms_eps = 1e-9           # for rms prop

        self.unseen = False  # change random seed to generate unseen example
        # Job objective
        self.objective_slowdown = "Job_Slowdown"

        self.objective_Ctime = "Job_Completion_Time"

        self.objective_disc = self.objective_slowdown
        self.dist = job_distribution.Dist(
            self.num_res, self.max_job_size, self.max_job_len)
        self.A2C_Ctime = {'agent': A2C, 'save_path': 'job_scheduling_A2C_Ctime',
                          'log_dir': "workspace/MultiBinary/tensor_A2C_Ctime/", 'color': 'Red', 'yerrcolor': 'Brown', 'title': 'A2C Ctime agent'}
        self.Tuned_A2C_Ctime = {'agent': A2C, 'save_path': 'job_scheduling_A2C_Ctime',
                             'log_dir': "workspace/MultiBinary/tensor_A2C_Ctime/", 'color': 'Orange', 'yerrcolor': 'Red', 'title': 'Tuned A2C Ctime agent'}
        self.A2C_Slowdown = {'agent': A2C, 'save_path': 'job_scheduling_A2C_Slowdown',
                             'log_dir': "workspace/MultiBinary/tensor_A2C_Slowdown/", 'color': 'SkyBlue', 'yerrcolor': 'Blue', 'title': 'A2C Slowdown agent'}
        self.Tuned_A2C_Slowdown = {'agent': A2C, 'save_path': 'job_scheduling_A2C_Slowdown',
                             'log_dir': "workspace/MultiBinary/tensor_A2C_Slowdown/", 'color': 'Blue', 'yerrcolor': 'Purple', 'title': 'Tuned A2C Slowdown agent'}
        self.PPO2_Slowdown = {'agent': PPO2, 'save_path': 'job_scheduling_PPO2_Slowdown', 'log_dir': "workspace/MultiBinary/tensor_PPO2_Slowdown/",
                     'color': 'Green', 'yerrcolor': 'DarkGreen', 'title': 'PPO2 Slowdown agent'}
        self.PPO2_Ctime = {'agent': PPO2, 'save_path': 'job_scheduling_PPO2_Ctime', 'log_dir': "workspace/MultiBinary/tensor_PPO2_Ctime/",
                     'color': 'chocolate', 'yerrcolor': 'brown', 'title': 'PPO2 Completion time agent'}
        self.random = {'agent': None, 'save_path': None, 'log_dir': None,
                       'color': 'Yellow', 'yerrcolor': 'Gold', 'title': 'Random agent'}
        self.SJF = {'agent': None, 'save_path': None, 'log_dir': None,
                    'color': 'pink', 'yerrcolor': 'Hotpink', 'title': 'SJF agent'}
        self.Packer = {'agent': None, 'save_path': None, 'log_dir': None,
                       'color': 'lime', 'yerrcolor': 'teal', 'title': 'Packer agent'}
        self.objective = self.A2C_Slowdown

        self.random_disc = {'agent': 'RandomAgent', 'save_path': None, 'color': 'r',
                            'title': 'Random Agent', 'load': None}
        self.SJF_disc = {'agent': 'SJF', 'save_path': None, 'color': 'orange',
                         'title': 'SJF', 'load': None}
        self.Packer_disc = {'agent': 'Packer', 'save_path': None, 'color': 'magenta',
                            'title': 'Packer', 'load': None}

        self.model_save_path = 'workspace/Discrete/hyperParamModels/'
        self.model_save_path_MB = 'workspace/MultiBinary/hyperParamModels/'

        # DQN
        self.DQN_SL = {'agent': 'DQN', 'save_path': self.model_save_path + "job_scheduling_" + "DQN" + "_" + self.objective_slowdown,
                       'color': 'g', 'title': 'DQN agent trained for SL', 'load': DQN}
        self.DQN_CT = {'agent': 'DQN', 'save_path': self.model_save_path + "job_scheduling_" + "DQN" + "_" + self.objective_Ctime,
                       'color': 'c', 'title': 'DQN agent trained for CT', 'load': DQN}
        # PPO2
        self.PPO2_SL = {'agent': 'PPO2', 'save_path': self.model_save_path + "job_scheduling_" + "PPO2" + "_" + self.objective_slowdown,
                        'color': 'm', 'title': 'PPO2 agent trained for SL', 'load': PPO2}
        self.PPO2_CT = {'agent': 'PPO2', 'save_path': self.model_save_path + "job_scheduling_" + "PPO2" + "_" + self.objective_Ctime,
                        'color': 'y', 'title': 'PPO2 agent trained for CT', 'load': PPO2}
        # A2C
        self.A2C_SL = {'agent': 'A2C', 'save_path': self.model_save_path + "job_scheduling_" + "A2C" + "_" + self.objective_slowdown,
                       'color': 'k', 'title': 'A2C agent trained for SL', 'load': A2C}
        self.A2C_CT = {'agent': 'A2C', 'save_path': self.model_save_path + "job_scheduling_" + "A2C" + "_" + self.objective_Ctime,
                       'color': 'b', 'title': 'A2C agent trained for CT', 'load': A2C}

    # Tuned_model_DQN_Job_Completion_Time.zip

        self.A2C_Tune_SL = {'agent': 'A2C_Tune_SL', 'save_path': self.model_save_path + "Tuned_model_A2C" + "_" + self.objective_slowdown,
                            'color': 'thistle', 'title': 'A2C Tune agent trained for SL', 'load': A2C}
        self.A2C_Tune_CT = {'agent': 'A2C_Tune_CT', 'save_path': self.model_save_path + "Tuned_model_A2C" + "_" + self.objective_Ctime,
                            'color': 'sienna', 'title': 'A2C Tune agent trained for CT', 'load': A2C}
        # PPO2 Tuned
        self.PPO2_Tune_SL = {'agent': 'PPO2_Tune_SL', 'save_path': self.model_save_path + "Tuned_model_PPO2" + "_" + self.objective_slowdown,
                             'color': 'thistle', 'title': 'PPO2 Tune agent trained for SL', 'load': PPO2}
        self.PPO2_Tune_CT = {'agent': 'PPO2_Tune_CT', 'save_path': self.model_save_path + "Tuned_model_PPO2" + "_" + self.objective_Ctime,
                             'color': 'sienna', 'title': 'PPO2 Tune agent trained for CT', 'load': PPO2}

        # DQN Tuned
        self.DQN_Tune_SL = {'agent': 'DQN_Tune_SL', 'save_path': self.model_save_path + "Tuned_model_DQN" + "_" + self.objective_slowdown,
                            'color': 'thistle', 'title': 'DQN Tune agent trained for SL', 'load': DQN}
        self.DQN_Tune_CT = {'agent': 'DQN_Tune_CT', 'save_path': self.model_save_path + "Tuned_model_DQN" + "_" + self.objective_Ctime,
                            'color': 'sienna', 'title': 'DQN Tune agent trained for CT', 'load': DQN}

        self.model_training_iterations = 100

        self.tensorBoard_DQN_Logs = 'workspace/Discrete/tensorBoardLogs/'
        self.tensorBoard_MB_Logs = 'workspace/MultiBinary/tensorBoardLogs/'

        self.localhost = '0.0.0.0'

        self.figure_path = 'workspace/Discrete/output/'

        self.figure_extension = '.png'
