import DeepRMEnv
import parameters
import numpy as np
import pandas as pd
from IPython.display import display

dataframe = pd.read_csv(
    "/home/aicon/kunalS/workspace/csvTest/container_usage.csv")
# print(dataframe.head(10))
np_array = dataframe.to_numpy()

n = 100
np_array = np_array[n:]
print("Trimimng the array to 100 elements for testing")

print("Sorting the input list with respect to job length")

new_np_array = sorted(np_array, key=lambda x: x[0])

pa = parameters.Parameters()
pa.job_wait_queue = 5
pa.simu_len = 100  # length of job sequence
# pa.simu_len = 10 # length of job sequence
pa.num_ex = 10
pa.new_job_rate = 1

job_sequence_len = []
job_sequence_size = []

# Creatingjoblengthforjobs

for i in range(len(new_np_array)):
    job_sequence_len.append(new_np_array[i][0])
    #print(new_np_array[i][0], end=' ')
    job_sequence_size.append([new_np_array[i][2], new_np_array[i][3]])
    #print(new_np_array[i][2], end=' ')
    #print(new_np_array[i][3], end=' ')

env = DeepRMEnv.Env(pa, job_sequence_len=job_sequence_len, job_sequence_size=job_sequence_size,
                    end='all_done')
env.reset()
# for i in  range(len(job_sequence_len)):
#     ob, reward, done, info = env.step(i)
#     print("--------------------------------------------------")
#     print("Iteration number :", i)
#     print("Jobs in waiting queue(M):",
#           ob[1], "\nReward:", reward, "\nDone:", done)
#     if done == True:
#         break




# print("Random Agent")
i = 0
while(1):
    i += 1
    ob, reward, done, info = env.step(np.random.randint(pa.job_wait_queue))
    print("--------------------------------------------------")
    print("Iteration number :", i)
    print("Jobs in waiting queue(M):",
          ob[1], "\nReward:", reward, "\nDone:", done)
    if done == True:
        break
