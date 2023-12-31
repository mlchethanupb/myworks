import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
#%matplotlib qt
import subprocess
import seaborn as sns


path = 'results'

ETSI = 1
F_100 = 0
F_300 = 0
F_500 = 0

# Python program to get average of a list
def Average(lst):
    return sum(lst) / len(lst)



def plot_ecdf(stat_name):


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


    import statistics
    print("len new list", len(new_list))
    print("Plotting graph")

    #"""
    #define figure size
    sns.set(rc={"figure.figsize":(15, 8)})
    ax = sns.ecdfplot(data=new_list)
    ax.legend(labels=['unmanaged', 'managed'])
    plt.plot(figsize=(15, 8), rot=0)
    #"""

    #ax.set_xlabel("Environmental Awareness Ratio")
    #ax.set_ylabel("EAR")
    fig_name = 'plots/' + stat_name + '_ecdf.pdf'
   
    if ETSI:
        ax.set_title("ETSI")
        #ax.set_ylabel("EAR")
        fig_name = 'plots/ecdf/' + stat_name + '_ETSI_ecdf.pdf'
    elif F_100:
        ax.set_title("Fixed 100ms")
        fig_name = 'plots/ecdf/' + stat_name + '_F_100_ecdf.pdf'
    elif F_300:
        ax.set_title("Fixed 300ms")
        fig_name = 'plots/ecdf/' + stat_name + '_F_300_ecdf.pdf'
    elif F_500:
        ax.set_title("Fixed 500ms")
        fig_name = 'plots/ecdf/' + stat_name + '_F_500_ecdf.pdf'

    plt.savefig(fig_name) 

def main():
    print("main")
    #plot_ecdf("EAR")
    #plot_ecdf("EteDelay")
    #plot_ecdf("objectAge")
    #plot_ecdf("timebwupdate")
    plot_ecdf("msgsize")
    #plot_ecdf("numCPMPerSec")


if __name__ == "__main__":
    main()
