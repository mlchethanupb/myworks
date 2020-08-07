import DeepRMEnv
import parameters
import numpy as np

print("UnitTestEnvironment")
pa = parameters.Parameters()
pa.job_wait_queue = 5
pa.simu_len = 100 # length of job sequence
# pa.simu_len = 10 # length of job sequence
pa.num_ex = 10
pa.new_job_rate = 1

job_sequence_len = []
job_sequence_size = []

#Creatingjoblengthforjobs
for i in range(100):
	job_sequence_len.append(np.random.randint(1,pa.time_horizon))

#Creatingtheresourcerequirementforjobs
for i in range(100):
	cpu_req=np.random.randint(1,pa.max_job_size)
	mem_req=np.random.randint(1,pa.max_job_size)
	job_sequence_size.append([cpu_req,mem_req])


env = DeepRMEnv.Env(pa,job_sequence_len=job_sequence_len,job_sequence_size=job_sequence_size , end = 'all_done')
env.reset()

print("Random Agent")
i= 0
while(1):
	i+=1
	ob , reward , done , info = env.step(np.random.randint(pa.job_wait_queue))
	print("--------------------------------------------------")
	print("Iteration number :", i)
	print("Jobs in waiting queue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
	if done == True:
		break

# print("Done with first set of inputs")
# env = DeepRMEnv.Env(pa,job_sequence_len=job_sequence_len[100:],job_sequence_size=job_sequence_size[100:] , end = 'all_done')
# while(1):
# 	i+=1
# 	ob , reward , done , info = env.step(np.random.randint(pa.job_wait_queue))
# 	print("--------------------------------------------------")
# 	print("Iteration number :", i)
# 	print("Jobs in waiting queue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# 	if done == True:
# 		break


# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
# env.step(5)
#
# print("Jobs are now in job slot and job backlog")
#
# ob,reward,done,info=env.step(0)
# print("Jobs in waiting queue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# ob,reward,done,info=env.step(1)
# print("Jobs in waiting queue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# ob,reward,done,info=env.step(2)
# print("Jobsinwaitingqueue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# ob,reward,done,info=env.step(3)
# print("Jobsinwaitingqueue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# ob,reward,done,info=env.step(4)
# print("Jobsinwaitingqueue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
# ob,reward,done,info=env.step(4)
# print("Jobsinwaitingqueue(M):",ob[1],"\nReward:",reward,"\nDone:",done)
