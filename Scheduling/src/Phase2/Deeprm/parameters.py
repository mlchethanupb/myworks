import numpy as np
import math
import job_distribution
from stable_baselines import DQN
from stable_baselines import PPO2
from stable_baselines import A2C
from stable_baselines import HER
from stable_baselines import GAIL
from stable_baselines import ACER
from stable_baselines import ACKTR
from stable_baselines import TRPO

class Parameters:
    def __init__(self):

        self.output_filename = 'data/tmp'

        self.num_epochs = 1000       # number of training epochs
        self.simu_len = 10             # length of the busy cycle that repeats itself
        self.num_ex = 1                # number of sequences

        self.output_freq = 10          # interval for output and store parameters

        self.num_seq_per_batch = 10    # number of sequences to compute baseline
        self.episode_max_length = 100  # enforcing an artificial terminal

        self.num_res = 2               # number of resources in the system
        self.num_nw = 5                # maximum allowed number of work in the queue

        self.time_horizon = 20         # number of time steps in the graph
        self.max_job_len = 15          # maximum duration of new jobs
        self.res_slot = 10             # maximum number of available resource slots
        self.max_job_size = 10         # maximum resource request of new work

        self.backlog_size = 60         # backlog queue size

        self.max_track_since_new = 10  # track how many time steps since last new jobs

        self.job_num_cap = 40          # maximum number of distinct colors in current work graph

        self.new_job_rate = 0.7        # lambda in new job arrival Poisson Process

        self.discount = 1           # discount factor

        # distribution for new job arrival
        self.dist = job_distribution.Dist(
            self.num_res, self.max_job_size, self.max_job_len)

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

        # supervised learning mimic policy
        self.batch_size = 10
        self.evaluate_policy_name = "SJF"

        self.objective_slowdown = "Job_Slowdown"

        self.objective_Ctime = "Job_Completion_Time"

        self.objective_deadline = "Job_Deadline"

        self.objective_disc = self.objective_slowdown

        self.random_disc = {'agent': 'Random', 'save_path': None, 'color': 'r', 'log_dir': None,
                            'title': 'Random Agent', 'load': None}
        self.SJF_disc = {'agent': 'SJF', 'save_path': None, 'color': 'orange', 'log_dir': None,
                         'title': 'SJF', 'load': None}
        self.Packer_disc = {'agent': 'Packer', 'save_path': None, 'color': 'magenta',  'log_dir': None,
                            'title': 'Packer', 'load': None}
        self.SJF_AICON = {'agent': 'SJF AICON', 'save_path': None, 'color': 'purple', 'log_dir': None,
                          'title': 'SJF AICON', 'load': None}
        self.Packer_AICON = {'agent': 'Packer AICON', 'save_path': None, 'color': 'hotpink',  'log_dir': None,
                             'title': 'Packer AICON', 'load': None}
        self.model_save_path = 'models/'
        self.DQN_SL = {'agent': 'DQN', 'save_path': self.model_save_path + "job_scheduling_" + "DQN",
                       'log_dir': self.model_save_path, 'color': 'g', 'title': 'Discrete - DQN agent trained for SL', 'load': DQN}
        self.PPO2_SL = {'agent': 'PPO2', 'save_path': self.model_save_path + "job_scheduling_" + "PPO2",
                        'log_dir': self.model_save_path, 'color': 'm', 'title': 'Discrete - PPO2 agent trained for SL', 'load': PPO2}
        self.A2C_SL = {'agent': 'A2C', 'save_path': self.model_save_path + "job_scheduling_" + "A2C",
                       'log_dir': self.model_save_path, 'color': 'k', 'title': 'Discrete - A2C agent trained for SL', 'load': A2C}
        self.HER_SL = {'agent': 'HER', 'save_path': self.model_save_path + "job_scheduling_" + "HER",
                       'log_dir': self.model_save_path, 'color': 'r', 'title': 'Discrete - HER agent trained for SL', 'load': HER}
        self.GAIL_SL = {'agent': 'GAIL', 'save_path': self.model_save_path + "job_scheduling_" + "GAIL",
                        'log_dir': self.model_save_path, 'color': 'r', 'title': 'Discrete - GAIL agent trained for SL', 'load': GAIL}
        self.TRPO_SL = {'agent': 'TRPO', 'save_path': self.model_save_path + "job_scheduling_" + "TRPO",
                        'log_dir': self.model_save_path, 'color': 'chocolate', 'title': 'Discrete - TRPO agent trained for SL', 'load': TRPO}
        self.A2C_Tuned_SL = {'agent': 'A2C', 'save_path': self.model_save_path + "Tune_A2C_Custom_Policy",
                             'log_dir': self.model_save_path, 'color': 'teal', 'title': 'Tuned A2C agent trained for SL', 'load': A2C}
        self.TRPO_Tuned_SL = {'agent': 'TRPO', 'save_path': self.model_save_path + "Tune_TRPO_Custom_Policy",
                              'log_dir': self.model_save_path, 'color': 'b', 'title': 'Tuned TRPO agent trained for SL', 'load': TRPO}

        self.train_path = 'output/train/'
        self.run_path = 'output/run/'
        self.figure_extension = '.png'
        self.tensorBoard_Logs = 'tensorboard/'

        self.ACER_SL = {'agent': 'ACER', 'save_path': self.model_save_path + "job_scheduling_" + "ACER",
                        'log_dir': self.model_save_path, 'color': 'k', 'title': 'Discrete - ACER agent trained for SL', 'load': ACER}

        self.ACKTR_SL = {'agent': 'ACKTR', 'save_path': self.model_save_path + "job_scheduling_" + "ACKTR",
                         'log_dir': self.model_save_path, 'color': 'm', 'title': 'Discrete - ACKTR agent trained for SL', 'load': ACKTR}

    def compute_dependent_parameters(self):
        # such that it can be converted into an image
        assert self.backlog_size % self.time_horizon == 0
        self.backlog_width = self.backlog_size / self.time_horizon
        self.network_input_height = self.time_horizon
        self.network_input_width = \
            (self.res_slot +
             self.max_job_size * self.num_nw) * self.num_res + \
            self.backlog_width + \
            1  # for extra info, 1) time since last new job
        self.network_input_width = int(self.network_input_width)
        print("Value of the self.network_input_width-> ",
              self.network_input_width)
        # compact representation
        self.network_compact_dim = (self.num_res + 1) * \
            (self.time_horizon + self.num_nw) + \
            1  # + 1 for backlog indicator + self.num_nw) + 1  # + 1 for backlog indicator

        self.network_output_dim = self.num_nw + 1  # + 1 for void action
