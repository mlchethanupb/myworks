import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
#%matplotlib qt
import subprocess
import seaborn as sns


path = 'results'

ETSI = 0
F_100 = 1
F_300 = 0
F_500 = 0




def plot_linegraph(stat_name):


    print("=======================================================================================")
    stat_id = stat_name + ':vector'
    print("Plotting bar graph for: ", stat_id)


    if ETSI:
        files_sca_csv = glob.glob(path + '/etsi/**/p100/*.vec.csv', recursive=True)
    elif F_100:
        files_sca_csv = glob.glob(path + '/fixed100ms/**/p100/*.vec.csv', recursive=True)
    elif F_300:
        files_sca_csv = glob.glob(path + '/fixed300ms/**/p100/*.vec.csv', recursive=True)
    elif F_500:
        files_sca_csv = glob.glob(path + '/fixed500ms/**/p100/*.vec.csv', recursive=True)
    else:
        files_sca_csv = glob.glob(path + '/**/p100/*.vec.csv', recursive=True)
    
    #files_sca_csv = glob.glob(path + '/**/p100/*.vec.csv', recursive=True)
    #print(files_sca_csv)
    files_sca_csv.sort()
    #print(files_sca_csv)
    print("Total Number of files: ",len(files_sca_csv))
    list_of_all=[]
    list_dict = {}
    final_list = []
    for file in files_sca_csv:
        print(file)
        f_split = file.split('-')
        
        df = pd.read_csv(file)
        earstat = df[(df.type=='vector') & (df.name==stat_id)]


        earstat = earstat[['vecvalue']]
        #print(earstat)
        splitted = earstat.vecvalue.str.split (' ')
        #print(splitted)

        list__ = list(splitted.apply(lambda x: x))
        #print(list__)
        final_list = []
        for item_list in list__:
            for item in item_list:
                final_list.append(float(item))

        if(None == list_dict.get(f_split[0], None)):
            list_dict[f_split[0]] = final_list
            print("-----------------------------------------------------------------------------")
            print("adding first list for", f_split[0])
        else:
            list_dict[f_split[0]] = list_dict[f_split[0]] + final_list
            print("APPENDING list for", f_split[0])

        
        list_of_all.append(final_list)
        del df       
        del earstat
        del splitted
        list__.clear()
        final_list.clear()
        
        #print("final list", final_list)
        #print(earstat.iloc[0,0])
        #np_arr = np.array(earstat.iloc[0,0]) 
        #print(np_arr)
        #print(np.mean(np_arr))
        
        """
        earstat = df[(df.type=='statistic') & (df.name=='EAR:stats')]
        #earstat = df[(df.type=='statistic') & (df.name=='EteDelay:stats')]
        earstat = earstat['mean']
        print(earstat.mean())
        """
        #print(splitted.at[538,'vecvalue'])

    print(list_dict.keys())
    print("list of all", len(list_of_all))
    new_list = []
    new_list = [v for v in list_dict.values()]
    print("len dict", len(list_dict))
    list_dict.clear()
    print("len dict", len(list_dict))
    files_sca_csv.clear()

    """
    import statistics
    print("len new list", len(new_list))
    print("Plotting graph")
    sns.set(rc={"figure.figsize":(15, 8)})
    ax = sns.ecdfplot(data=new_list)
    ax.legend(labels=['unmanaged', 'managed'])
    
    #"""
    lst_to_plot = new_list[0]
    if not stat_name == "numCPMPerSec":
        q25, q75 = np.percentile(lst_to_plot, [25, 75])
        bin_width = 2 * (q75 - q25) * len(lst_to_plot) ** (-1/3)
        print(max(lst_to_plot),min(lst_to_plot))
        total_bins = int(round((max(lst_to_plot) - min(lst_to_plot)) / bin_width))
        print("Freedman–Diaconis number of bins:", total_bins)


    sns.set(rc={"figure.figsize":(15, 8)})
    
   
    #ax.set_xlabel("CPM Samples")
    if(stat_name == 'periodicity'):
        ax = sns.histplot(data=lst_to_plot, stat="percent", bins = total_bins)
        ax.set_title("Periodicity of CPM messages")
    elif(stat_name == 'msgsize'):
        ax = sns.histplot(data=lst_to_plot, stat="percent", bins = total_bins)
        ax.set_title("Message size of CPM message")
    elif(stat_name == 'numCPMPerSec'):
        ax = sns.histplot(data=lst_to_plot, stat="frequency", bins = 10)
        ax.set_title("Number of CPM messages generater Per second")


    if ETSI:
        #ax.set_title("ETSI")
        #ax.set_ylabel("EAR")
        
        fig_name = 'plots/' + stat_name + '_ETSI_histogram.pdf'
    elif F_100:
        #ax.set_title("Fixed 100ms")
        fig_name = 'plots/' + stat_name + '_F_100_histogram.pdf'
    elif F_300:
        #ax.set_title("Fixed 300ms")
        fig_name = 'plots/' + stat_name + '_F_300_histogram.pdf'
    elif F_500:
        #ax.set_title("Fixed 500ms")
        fig_name = 'plots/' + stat_name + '_F_500_histogram.pdf'
    else:
        print("Default use case of ETSI")
        fig_name= 'plots/' + stat_name + 'etsi_default_histogram.pdf'



    plt.plot(figsize=(15, 8), rot=0)
    plt.savefig(fig_name)

def main():
    print("main")
    #plot_linegraph("periodicity")
    plot_linegraph("msgsize")
    #plot_linegraph("numCPMPerSec")

if __name__ == "__main__":
    main()
