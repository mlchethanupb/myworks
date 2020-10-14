import MultiBinaryDeepRM
import parameters
import job_distribution
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines import PPO2, A2C
from stable_baselines.common import make_vec_env
import Script
from statistics import mean

# labeling the bar graph
def autolabel(rects, z):
    i = 0
    for rect in rects:
        height = rect.get_height()
        if height > 0:
            ax.text(rect.get_x() + rect.get_width()/2., height + z[i], '%.2f' % height, ha='center', va='bottom')
        i = i+1


def lenVsSD(x, y, z, model):    
    opacity = 0.8
    agent_plots = []

    agent_plot = plt.bar(x, y, yerr=z, ecolor=models[i]['yerrcolor'], capsize=9,
         alpha=opacity, color=model['color'], label=model['title'])
    agent_plots.append(agent_plot)

    for agent_plot in agent_plots:
        autolabel(agent_plot, z)

    plt.xlabel('Job length')
    plt.ylabel('Job Slowdown')
    plt.title('Slowdown vs. job length')
    plt.xticks(x)
    plt.legend()
    plt.show()
    fig.savefig('workspace/SDVsJobLen.png')

if __name__ == '__main__':
    pa = parameters.Parameters()
    models = [pa.A2C_Slowdown]
    pa.cluster_load = 1.1
    pa.num_episode = 10
    pa.simu_len, pa.new_job_rate = job_distribution.compute_simulen_and_arrival_rate(pa.cluster_load ,pa)     
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = MultiBinaryDeepRM.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)
    all_allocated_jobs = []
    for i in range(len(models)):
        pa.objective = models[i]
        log_dir = models[i]['log_dir']
        save_path = None
        model = None
        if models[i]['save_path'] != None:
            save_path = log_dir + models[i]['save_path']
            model = models[i]['agent'].load(save_path, env1)
        episode, reward, slowdown, completion_time, withheld_jobs, allocated_jobs = Script.run_episodes(model, pa, env, job_sequence_len)
        all_allocated_jobs.append(allocated_jobs)

    all_len_SD = []
    for i in range(len(models)):
        temp = []
        for k in range(int(pa.max_job_len)): 
            temp.append([])
        all_len_SD.append(temp)

    for i in range(len(models)):
        for j in range(len(all_allocated_jobs[i])):
            for k in range(int(pa.max_job_len)): 
                if all_allocated_jobs[i][j].len == k+1:
                    all_len_SD[i][k].append(all_allocated_jobs[i][j].job_slowdown)

    fig, ax = plt.subplots()
    x = ()
    y = ()
    z = ()

    for i in range(len(models)):
        for j in range(len(all_len_SD[i])):
            if all_len_SD[i][j] != []:
                x = x + (j+1,)
                y = y + (mean(all_len_SD[i][j]),)
                z = z + (np.std(all_len_SD[i][j]),)

        lenVsSD(x, y, z, models[i])