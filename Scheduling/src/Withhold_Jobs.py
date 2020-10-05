import tensorflow as tf
import numpy as np
import Deeprm1
import parameters
import job_distribution
import matplotlib.pyplot as plt
import numpy as np
import math
import matplotlib.pyplot as plt
import argparse
from random import sample
import os
import gym
from stable_baselines import PPO2, A2C
from collections import Counter
from stable_baselines.common.env_checker import check_env
from gym import spaces
from stable_baselines.common import make_vec_env
import Randomscheduler
import warnings
import random
import Script
from statistics import mean
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

# labeling the bar graph
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        if height > 0:
            ax.text(rect.get_x() + rect.get_width()/2., height, '%.2f' % height, ha='center', va='bottom')
            ax.text(rect.get_x() + rect.get_width()/2., height, '%.2f' % height, ha='center', va='bottom')

def len_withheld_jobs(x, y):    
    opacity = 0.8
    agent_plots = []

    agent_plot = plt.bar(x, y,  
         alpha=opacity, color=pa.A2C_Slowdown['color'], label=pa.A2C_Slowdown['title'])
    agent_plots.append(agent_plot)

    for agent_plot in agent_plots:
        autolabel(agent_plot)

    plt.xlabel('job length')
    plt.ylabel('Fraction')
    plt.title('length of withheld jobs')
    plt.xticks(x)
    plt.legend()
    plt.show()
    fig.savefig('workspace/WithheldJobs.png')

if __name__ == '__main__':
    pa = parameters.Parameters()
    pa.cluster_load = 1.1
    pa.objective = pa.A2C_Slowdown
    pa.simu_len, pa.new_job_rate = job_distribution.compute_simulen_and_arrival_rate(pa.cluster_load ,pa)     
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)
    
    log_dir = pa.A2C_Slowdown['log_dir']
    save_path = log_dir + pa.A2C_Slowdown['save_path']
    model = pa.A2C_Slowdown['agent'].load(save_path, env1)
    episode, reward, slowdown, completion_time, withheld_jobs, allocated_jobs = Script.run_episodes(model, pa, env, job_sequence_len)

    withheld_job_len=[]
    for k in range(len(withheld_jobs)):
        withheld_job_len.append(withheld_jobs[k].len)
    
    # data to plot
    x = ()
    y = ()
    fig, ax = plt.subplots()
    if len(withheld_job_len) != 0:
        for i in range(int(pa.max_job_len)):
            x = x + (i+1,)
            y = y + (withheld_job_len.count(i+1)/len(withheld_job_len),)
        len_withheld_jobs(x,y)
        print("Jobs were withheld")
    else:
        print("Jobs were not withheld")