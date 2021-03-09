import numpy as np
import _pickle as cPickle
import matplotlib.pyplot as plt
import numpy as np
import environment
import parameters
import pg_network
import other_agents


def discount(x, gamma):
    """
    Given vector x, computes a vector y such that
    y[i] = x[i] + gamma * x[i+1] + gamma^2 x[i+2] + ...
    """
    out = np.zeros(len(x))
    out[-1] = x[-1]
    for i in reversed(range(len(x)-1)):
        out[i] = x[i] + gamma*out[i+1]
    assert x.ndim >= 1
    # More efficient version:
    # scipy.signal.lfilter([1],[1,-gamma],x[::-1], axis=0)[::-1]
    return out


def categorical_sample(prob_n):
    """
    Sample from categorical distribution,
    specified by a vector of class probabilities
    """
    prob_n = np.asarray(prob_n)
    csprob_n = np.cumsum(prob_n)
    return (csprob_n > np.random.rand()).argmax()


def get_traj(test_type, pa, env, episode_max_length, pg_resume=None, render=False):
    """
    Run agent-environment loop for one whole episode (trajectory)
    Return dictionary of results
    """

    if test_type == 'PG':  # load trained parameters

        pg_learner = pg_network.PGLearner(pa)

        net_handle = open(pg_resume, 'rb')
        net_params = cPickle.load(net_handle)
        pg_learner.set_net_params(net_params)

    env.reset()
    rews = []

    ob = env.observe()

    for _ in range(episode_max_length):

        if test_type == 'PG':
            a = pg_learner.choose_action(ob)

        elif test_type == 'Tetris':
            a = other_agents.get_packer_action(env.machine, env.job_slot)

        elif test_type == 'SJF':
            a = other_agents.get_sjf_action(env.machine, env.job_slot)

        elif test_type == 'Random':
            a = other_agents.get_random_action(env.job_slot)

        ob, rew, done, info = env.step(a, repeat=True)

        rews.append(rew)

        if done: break
        if render: env.render()
        # env.render()

    return np.array(rews), info


def launch(pa, pg_resume=None, render=False, plot=False, repre='image', end='no_new_job'):

    # ---- Parameters ----

    test_types = ['Tetris', 'SJF', 'Random']

    if pg_resume is not None:
        test_types = ['PG'] + test_types

    env = environment.Env(pa, render, repre=repre, end=end)

    all_discount_rews = {}
    jobs_slow_down = {}
    work_complete = {}
    work_remain = {}
    job_len_remain = {}
    num_job_remain = {}
    job_remain_delay = {}

    for test_type in test_types:
        all_discount_rews[test_type] = []
        jobs_slow_down[test_type] = []
        work_complete[test_type] = []
        work_remain[test_type] = []
        job_len_remain[test_type] = []
        num_job_remain[test_type] = []
        job_remain_delay[test_type] = []

    for seq_idx in range(pa.num_ex):
        print('\n\n')
        print("=============== " + str(seq_idx) + " ===============")

        for test_type in test_types:

            rews, info = get_traj(test_type, pa, env, pa.episode_max_length, pg_resume)

            print("---------- " + test_type + " -----------")

            print("total discount reward : \t %s" % (discount(rews, pa.discount)[0]))

            all_discount_rews[test_type].append(
                discount(rews, pa.discount)[0]
            )

            # ------------------------
            # ---- per job stat ----
            # ------------------------

            enter_time = np.array([info.record[i].enter_time for i in range(len(info.record))])
            finish_time = np.array([info.record[i].finish_time for i in range(len(info.record))])
            job_len = np.array([info.record[i].len for i in range(len(info.record))])
            job_total_size = np.array([np.sum(info.record[i].res_vec) for i in range(len(info.record))])

            finished_idx = (finish_time >= 0)
            unfinished_idx = (finish_time < 0)

            jobs_slow_down[test_type].append(
                (finish_time[finished_idx] - enter_time[finished_idx]) / job_len[finished_idx]
            )
            work_complete[test_type].append(
                np.sum(job_len[finished_idx] * job_total_size[finished_idx])
            )
            work_remain[test_type].append(
                np.sum(job_len[unfinished_idx] * job_total_size[unfinished_idx])
            )
            job_len_remain[test_type].append(
                np.sum(job_len[unfinished_idx])
            )
            num_job_remain[test_type].append(
                len(job_len[unfinished_idx])
            )
            job_remain_delay[test_type].append(
                np.sum(pa.episode_max_length - enter_time[unfinished_idx])
            )

        env.seq_no = (env.seq_no + 1) % env.pa.num_ex

    # -- matplotlib colormap no overlap --
    if plot:

        # Keep it
        def autolabel(rects , ax) :
            for rect in rects :
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width() / 2. , height ,
                    '%.1f' % height , ha = 'center' , va = 'bottom')

        fig = plt.figure()
        n_groups = 2
        fig , ax = plt.subplots(figsize = (20 , 5) , dpi = 100)
        index = np.arange(n_groups)
        bar_width = 0.1
        opacity = 0.8
        agent_plots = []
        colors = ['r', 'c','m','y']
        title = ['DeepRM', 'Packer', 'SJF' ,'Random']
        for i in range(len(test_types)) :
            mean_slowdown = []
            mean_ctime = []
            print(test_types[i])
            value_sl = jobs_slow_down.get(test_types[i])
            value_ct = work_complete.get(test_types[i])
            for val in range(len(value_sl)):
                mean_slowdown.append(np.mean(value_sl[val]))
                mean_ctime.append(np.mean(value_ct[val]))
                # mean_ctime.append(np.mean(jobs_completion_time[i][val]))
            # Changed here for objective
            # mean_values = (np.mean(jobs_slow_down[i]) , np.mean(jobs_completion_time[i]))
            # deviation = (np.std(jobs_slow_down[i]) , np.std(jobs_completion_time[i]))
            # mean_values = (np.mean(mean_slowdown) , np.mean(mean_ctime))
            # deviation = (np.std(mean_slowdown) , np.std(mean_ctime))
            mean_values = (np.mean(mean_slowdown) , np.mean(mean_slowdown))
            deviation = (np.std(mean_slowdown) , np.std(mean_slowdown))
            agent_plot = plt.bar(index + i * bar_width , mean_values , bar_width ,
                                yerr = deviation ,
                                ecolor = 'k' ,
                                capsize = 14 ,
                                alpha = opacity ,
                                color = colors[i] ,
                                label = title[i])
            agent_plots.append(agent_plot)
        for agent_plot in agent_plots :
            autolabel(agent_plot , ax)

        plt.xlabel('Performance metrics')
        plt.ylabel('Average job slowdown')
        plt.title('Performance for different objective')
        plt.xticks(index + 4 * bar_width , ('Average job slowdown' ,
                                            'Average job completion time'))
        plt.legend()
        ax2 = ax.twinx()
        plt.ylabel("Average job completion time")
        ax2.set_ylim(ax.get_ylim())
        plt.tight_layout()

        plt.tight_layout()
        fig.savefig( "Performance_all.png")
        # Keep it

        num_colors = len(test_types)
        cm = plt.get_cmap('gist_rainbow')
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # ax.set_color_cycle([cm(1. * i / num_colors) for i in range(num_colors)])
        colors = ['k','r','g','b','c','m','y','orchid']

        i = 0
        for test_type in test_types:
            slow_down_cdf = np.sort(np.concatenate(jobs_slow_down[test_type]))
            slow_down_yvals = np.arange(len(slow_down_cdf))/float(len(slow_down_cdf))
            ax.plot(slow_down_cdf, slow_down_yvals, linewidth=2, label=test_type, color = colors[i])
            i += 1
        plt.legend(loc=4)
        plt.xlabel("job slowdown", fontsize=20)
        plt.ylabel("CDF", fontsize=20)
        # plt.show()
        plt.savefig(pg_resume + "_slowdown_fig" + ".png")

    return all_discount_rews, jobs_slow_down


def main():
    pa = parameters.Parameters()

    pa.simu_len = 200  # 5000  # 1000
    pa.num_ex = 10  # 100
    pa.num_nw = 10
    pa.num_seq_per_batch = 20
    # pa.max_nw_size = 5
    # pa.job_len = 5
    pa.new_job_rate = 0.3
    pa.discount = 1

    pa.episode_max_length = 20000  # 2000

    pa.compute_dependent_parameters()

    render = False

    plot = True  # plot slowdown cdf

    pg_resume = None
    pg_resume = 'data/pg_re_discount_1_rate_0.3_simu_len_200_num_seq_per_batch_20_ex_10_nw_10_1450.pkl'
    # pg_resume = 'data/pg_re_1000_discount_1_5990.pkl'
    pg_resume = 'data/tmp_2.pkl'

    pa.unseen = True

    launch(pa, pg_resume, render, plot, repre='image', end='all_done')


if __name__ == '__main__':
    main()
