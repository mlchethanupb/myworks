import glob
from os import stat
import pandas as pd
import numpy as np
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

    files_sca_csv = glob.glob(path + '/**/p100/*.sca.csv', recursive=True)

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
    
        values_mean = earstat['mean'].tolist()
        values_count = earstat['count'].tolist()
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
            df_avg.at[prev_row_name,prev_col_name] = Average(lst_mean,lst_count)
            df_ci.at[prev_row_name,prev_col_name] = calculate_ci(avg_stddev(lst_stddev, lst_count), sum(lst_count))


    
    print(df_avg)
    print(df_ci)
    print("Calculaton done, plotting graph")



    df3 = df_avg[['etsi_mode3', 'etsi_mode4', 'fixed100ms_mode3', 'fixed100ms_mode4', 'fixed300ms_mode3', 'fixed300ms_mode4', 'fixed500ms_mode3', 'fixed500ms_mode4']]
    print(df3)

    data = [{"M":df3.iloc[0]['etsi_mode3'],"U":df3.iloc[0]['etsi_mode4']},
            {"M":df3.iloc[0]['fixed100ms_mode3'],"U":df3.iloc[0]['fixed100ms_mode4']},
            {"M":df3.iloc[0]['fixed300ms_mode3'],"U":df3.iloc[0]['fixed300ms_mode4']},
            {"M":df3.iloc[0]['fixed500ms_mode3'],"U":df3.iloc[0]['fixed500ms_mode4']}]

    print(data)
    patterns = [ "//" , "oo"]
    df4 = pd.DataFrame(data,index=["etsi", "fixed 100ms", "fixed 300ms","fixed 500ms"])
    print(df4)
    bars = df4.plot(kind="bar", grid=False, legend = True, figsize=(15, 10), rot=0, facecolor='none', edgecolor='black')
    #df3.plot(kind="bar",yerr = df_ci, grid=False, legend = True, figsize=(15, 8), rot=0)#fontsize = 28
    
    print(len(bars.patches))

    for index, patch in enumerate(bars.patches):
        if(index < 4):
            patch.set_hatch(patterns[0])
        else:
            patch.set_hatch(patterns[1])

       
    if stat_name == 'EAR':
        plt.ylabel("Environmental Awareness Ratio")
    elif stat_name == 'EteDelay':
        plt.ylabel("End to End Delay")
    elif stat_name == 'objectAge':
        plt.ylabel("Age of Information")
    elif stat_name == 'timebwupdate':
        plt.ylabel("Time Between Update")
    else:
        plt.ylabel(stat_name)

    #plt.ylabel(stat_name)
    plt.xlabel("Message generation models")
    plt.legend(["Managed", "Unmanaged"],fontsize = 20)
    #ax.set_ylabel("EAR")
    fig_name = 'plots/' + stat_name + '_bargraph.pdf'
    plt.savefig(fig_name) 
    #plt.show()

def main():
    print("main")
    plot_bargraph('EteDelay')
    plot_bargraph('EAR')
    plot_bargraph('objectAge')
    plot_bargraph('timebwupdate')




if __name__ == "__main__":
    main()
