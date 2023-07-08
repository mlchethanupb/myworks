import glob
from os import stat
import matplotlib
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
#%matplotlib inline
#%matplotlib qt
import subprocess
import seaborn as sns
import re
import time
import math 

path = 'results'


# Python program to get average of a list
def Average(lst_avg, lst_count):

    avg_value = 0.0
    total_count = sum(lst_count)
    if len(lst_avg) == len(lst_count):
        for a_val, cnt_val in zip(lst_avg,lst_count):
            if(pd.isna(a_val) or pd.isna(cnt_val)):
                ...#print("values is nan, skipping")
            else:
                avg_value = avg_value + ((a_val*cnt_val)/total_count)
    else:
        print("lst_avg and lst_count length or not equal, cross check")

    return avg_value

def avg_stddev(lst_stddev, lst_count):
    total_groups = len(lst_count)
    avg_sd_val = 0.0

    if len(lst_stddev) == len(lst_count):
        sum_sq_sd = sum(i*i for i in lst_stddev if (pd.isna(i) == False))
        avg_sd_val = math.sqrt(sum_sq_sd/total_groups)
    else:
        print("lst_stddev and lst_count length or not equal, cross check")
    
    return avg_sd_val

def calculate_ci(avg_sd, total_count):
    return (1.96 * avg_sd/math.sqrt(total_count))

def add_values(lstvalues, value):
    for v in value:
        lstvalues.append(v)

def plot_bargraph(stat_name):

    print("=======================================================================================")
    stat_id = stat_name + ':stats'
    print("Plotting bar graph for: ", stat_id)

    files_sca_csv = glob.glob(path + '/**/*.sca.csv', recursive=True)

    df_rows = []
    df_cols = []
    for file in files_sca_csv:
        #print(file)
        f_split = file.split('/')
        #print(f_split)
        #col_name=f_split[2] + "_" + f_split[3] + "_" + f_split[4]
        col_name=f_split[1] + "_" + f_split[2]
        #print(col_name)
        if col_name not in df_cols:
            df_cols.append(col_name)
            #print(df_cols)
    
        row_name = f_split[-2]
        num = re.findall('\d+',row_name)
        row_name = num[0]
        if row_name not in df_rows:
            df_rows.append(row_name)
            #print(df_rows)
    
    df_cols.sort()
    print("columns", df_cols)
    df_rows.sort(key=int)
    print("rows",df_rows )
    #df_rows.insert(3, df_rows.pop(1))

    df_avg = pd.DataFrame(index=df_rows, columns=df_cols)
    df_ci = pd.DataFrame(index=df_rows, columns=df_cols)
    print(df_avg)

    prev_col_name = ""
    prev_row_name = ""
    lst_mean = []
    lst_count = []
    lst_stddev = []

    for file in files_sca_csv:
        f_split = file.split('/')
        col_name=f_split[1] + "_" + f_split[2]
        #col_name=f_split[2] + "_" + f_split[3] + "_" + f_split[4]
        row_name = f_split[-2]
        num = re.findall('\d+',row_name)
        row_name = num[0]

        df = pd.read_csv(file)
        earstat = df[(df.type=='statistic') & (df.name==stat_id)]
        earstat.dropna()

        if(stat_name == "numDelayedCPM"):
            print("entered 1")
            values_mean = earstat['mean'].tolist()
        else:
            values_mean = earstat['mean'].tolist()
        
        values_count = earstat['count'].tolist()
        print(values_count)
        values_stddev = earstat['stddev'].tolist()

        if sum(values_count) == 0:
            continue

        #print(col_name, row_name, values.mean())
        """
        print("====================================================================================")
        print(col_name, row_name)
        print("values_mean: ",values_mean)
        print("values_count: ",values_count)
        print("values_stddev: ",values_stddev)
        print("====================================================================================")
        """
        if not prev_col_name and not prev_row_name:
            #first time
            prev_col_name = col_name
            prev_row_name = row_name
            add_values(lst_mean, values_mean)
            add_values(lst_count, values_count)
            add_values(lst_stddev, values_stddev)
            
        elif prev_col_name == col_name and prev_row_name == row_name:
            #duplicate cases
            add_values(lst_mean, values_mean)
            add_values(lst_count, values_count)
            add_values(lst_stddev, values_stddev)
        else:
            #new cases; before loading new values calculate for previous col and row
            #print("====================================================================================")
            #print(prev_row_name, prev_col_name)
            if(stat_name == "numDelayedCPM"):
                print("entered 2")
                df_avg.at[prev_row_name,prev_col_name] = sum(lst_count)
            else:
                df_avg.at[prev_row_name,prev_col_name] = Average(lst_mean,lst_count)
            
            df_ci.at[prev_row_name,prev_col_name] = calculate_ci(avg_stddev(lst_stddev, lst_count), sum(lst_count))
            #print("====================================================================================")
            prev_col_name = col_name
            prev_row_name = row_name
            lst_mean.clear()
            lst_count.clear()
            lst_stddev.clear()
            add_values(lst_mean, values_mean)
            add_values(lst_count, values_count)
            add_values(lst_stddev, values_stddev)

        if(file ==  files_sca_csv[-1]):
            if(stat_name == "numDelayedCPM"):
                print("entered 3")
                df_avg.at[prev_row_name,prev_col_name] = sum(lst_count)
            else:
                df_avg.at[prev_row_name,prev_col_name] = Average(lst_mean,lst_count)
          
            df_ci.at[prev_row_name,prev_col_name] = calculate_ci(avg_stddev(lst_stddev, lst_count), sum(lst_count))


    print("printing average")
    print(df_avg)
    print(df_ci)
    print("Calculaton done, plotting graph")



    df_mg = df_avg[['etsi_mode3', 'fixed100ms_mode3',  'fixed300ms_mode3',  'fixed500ms_mode3']]
    df_unmg = df_avg[['etsi_mode4', 'fixed100ms_mode4',  'fixed300ms_mode4', 'fixed500ms_mode4']]

    
    print(df_mg)
    print(df_unmg)

    matplotlib.rc('xtick', labelsize=20) 
    matplotlib.rc('ytick', labelsize=20) 
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10), sharex=True, sharey=True)
    

    df_mg.plot(ax = ax1, legend=False)
    ax1.set_title("Managed mode", fontsize = 20)
    df_unmg.plot(ax = ax2, legend=False)
    ax2.set_title("Unmanaged mode", fontsize = 20)
    #df3.plot(kind="bar",yerr = df_ci, grid=False, legend = True, figsize=(15, 8), rot=0)#fontsize = 28

    
    for ax in fig.get_axes(): 
        markers = ["o","x","^","*"]
        ln_style = ['-', '--', '-.', ':']
        for i, l in enumerate(ax.get_lines()):
            l.set_marker(markers[i])
            l.set_ls(ln_style[i])
            l.set_lw(2)

        if stat_name == 'EAR':
            ax.set_ylabel("Environmental Awareness Ratio", fontsize = 20)
        elif stat_name == 'EteDelay':
            ax.set_ylabel("End to End Delay",  fontsize = 20) 
        elif stat_name == 'objectAge':
            ax.set_ylabel("Age of Information",  fontsize = 20)
        elif stat_name == 'timebwupdate':
            ax.set_ylabel("Time Between Update",  fontsize = 20)
        else:
            ax.set_ylabel(stat_name,  fontsize = 20)

        #plt.ylabel(stat_name)
        ax.set_xlabel("Vehicle penetration rate [%]", fontsize = 20)
    
    # Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in fig.get_axes():
        ax.label_outer()

    plt.legend(["ETSI", "Fixed 100ms", "Fixed 300ms" , "Fixed 500ms"],loc= (-0.4,1.01),fontsize = 20)
    fig_name = 'plots/' + stat_name + '_m_u_line.pdf'
    
    plt.savefig(fig_name, bbox_inches='tight') 
    #plt.show()

def main():
    print("main")
    #plot_bargraph('EteDelay')
    #plot_bargraph('EAR')
    #plot_bargraph('objectAge')
    #plot_bargraph('timebwupdate')
    plot_bargraph('numDelayedCPM')

if __name__ == "__main__":
    main()
