import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
#%matplotlib qt
import subprocess
import seaborn as sns
import re
import time

path = 'results'


# Python program to get average of a list
def Average(lst):
    return sum(lst) / len(lst)

def add_values(lstvalues, value):
    if pd.isna(value):
        ...#lstvalues.append(0)
    else:
        lstvalues.append(value)

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

	df2 = pd.DataFrame(index=df_rows, columns=df_cols)
	print(df2)

	prev_col_name = ""
	prev_row_name = ""
	lstvalues = []

	for file in files_sca_csv:
	    f_split = file.split('/')
	    col_name=f_split[1] + "_" + f_split[2]
	    #col_name=f_split[2] + "_" + f_split[3] + "_" + f_split[4]
	    row_name = f_split[-2]
	    num = re.findall('\d+',row_name)
	    row_name = num[0]

	    df = pd.read_csv(file)
	    earstat = df[(df.type=='statistic') & (df.name==stat_id)]
	
	    values = earstat['mean']
	    #print(col_name, row_name, values.mean())
	
	    if not prev_col_name and not prev_row_name:
	        prev_col_name = col_name
	        prev_row_name = row_name
	        add_values(lstvalues, values.mean())
	    elif prev_col_name == col_name and prev_row_name == row_name:
	        add_values(lstvalues, values.mean())
	    else:
	        prev_col_name = col_name
	        prev_row_name = row_name
	        lstvalues.clear()
	        add_values(lstvalues, values.mean())
	
	    #print(lstvalues)
	    df2.at[row_name,col_name] = Average(lstvalues)

	
	print(df2)
	print("Calculaton done, plotting graph")



	df3 = df2[['etsi_mode3', 'etsi_mode4', 'fixed100ms_mode3', 'fixed100ms_mode4', 'fixed300ms_mode3', 'fixed300ms_mode4', 'fixed500ms_mode3', 'fixed500ms_mode4']]
	print(df3)

	df3.plot(kind="bar",figsize=(15, 8), rot=0)
	plt.ylabel("ETE")
	plt.xlabel("Vehicle Penetration rate")
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