import numpy as np
import math
import matplotlib.pyplot as plt
import parameters
import argparse
from random import sample
import os
import gym
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines import PPO2
from stable_baselines.common.env_checker import check_env		
from gym import spaces	



class Env(gym.Env):
	def __init__(self , pa , job_sequence_len = None , job_sequence_size = None , end = 'no_new_job') :
		super(Env, self).__init__()
		self.pa = pa
		self.end = end  # termination type, 'no_new_job' or 'all_done'
		self.curr_time = 0
		self.job_sequence_len = job_sequence_len
		self.job_sequence_size = job_sequence_size
		self.seq_no = 0  # which example sequence
		self.seq_idx = 0  # index in that sequence
		
		# initialize system
		self.machine = Machine(pa)
		self.job_slot = JobSlot(pa)
		self.job_backlog = JobBacklog(pa)
		self.job_record = JobRecord()
		state_space = self.observe()
		low_state_space = [[],[]]
		high_state_space = [[],[]]
		low_state_space[0] = state_space[1]
		low_state_space[1] = state_space[1]
		high_state_space[0] = state_space[0]
		high_state_space[1] = [element * 2 for element in state_space[0]]
		self.low_state = np.array(low_state_space)
		self.high_state = np.array(high_state_space)
		print("self.high_state",self.high_state)

		action_space = 6
		self.state_space = state_space
		self.action_space = spaces.Discrete(action_space)
		self.observation_space = spaces.Box(low = self.low_state, high = self.high_state, dtype=np.int64)
	
	def step(self , a) :
		status = None
		done = False
		reward = 0
		info = {}
		if a == self.pa.job_wait_queue :  # explicit void action
			status = 'MoveOn'
		elif self.job_slot.slot[a] is None :  # implicit void action
			status = 'MoveOn'
		else :
			allocated = self.machine.allocate_job(self.job_slot.slot[a] , self.curr_time)
			if not allocated :  # implicit void action
				status = 'MoveOn'
			else :
				status = 'Allocate'
		
		if status == 'MoveOn' :
			self.curr_time += 1
			self.machine.time_proceed(self.curr_time)
			
			if self.end == "no_new_job" :  # end of new job sequence
				if self.seq_idx >= self.pa.simu_len :
					done = True
			elif self.end == "all_done" :
				# Done is true if no jobs are running in th machine + no job in the waiting queue and
				# no jobs in the backlog
				if self.seq_idx >= self.pa.simu_len and len(self.machine.running_job) == 0 and \
						all(s is None for s in self.job_slot.slot) and \
						all(s is None for s in self.job_backlog.backlog) :
					done = True
				# Deadlock handling
				elif self.curr_time > self.pa.episode_max_length :  # run too long, force termination
					done = True
			
			if not done :
				if self.seq_idx < self.pa.simu_len :  # otherwise, end of new job sequence, i.e. no new jobs
					new_job = self.get_new_job_from_seq(self.seq_no , self.seq_idx)
					self.seq_idx += 1
					if new_job.len > 0 :
						add_to_backlog = True
						# If the job slot is empty then only put the new job in the job slot/waiting queue
						# If the job slot is not empty then the job will go in the job backlog
						for i in range(self.pa.job_wait_queue) :
							if self.job_slot.slot[i] is None :  # put in new visible job slots
								self.job_slot.slot[i] = new_job
								self.job_record.record[new_job.id] = new_job
								add_to_backlog = False
								break
                                
						if add_to_backlog :
							if self.job_backlog.curr_size < self.pa.backlog_size :
								self.job_backlog.backlog[self.job_backlog.curr_size] = new_job
								self.job_backlog.curr_size += 1
								self.job_record.record[new_job.id] = new_job
							else :  # abort, backlog full
								print("Backlog full.")
			reward = self.get_reward()
		
		elif status == 'Allocate' :
			self.job_record.record[self.job_slot.slot[a].id] = self.job_slot.slot[a]
			self.job_slot.slot[a] = None
			
			# dequeue backlog
			if self.job_backlog.curr_size > 0 :
				self.job_slot.slot[a] = self.job_backlog.backlog[0]  # if backlog empty, it will be 0
				self.job_backlog.backlog[: -1] = self.job_backlog.backlog[1 :]
				self.job_backlog.backlog[-1] = None
				self.job_backlog.curr_size -= 1
		
		ob = self.observe()
		if done :
			self.seq_idx = 0
			self.seq_no = 0
			self.reset()
		return ob , reward , done , info
	
	# Get new job from waiting queue
	def get_new_job_from_seq(self , seq_no , seq_idx) :
		new_job = Job(resorce_requirement = self.job_sequence_size[seq_idx] ,job_len = self.job_sequence_len[seq_idx] ,job_id = len(self.job_record.record) ,enter_time = self.curr_time)
		return new_job
	
	def observe(self) :
		ob = [[],[]]

		# Current allocation of cluster resources
		ob[0] = list(self.machine.available_res_slot)
		
		#The resource profile of jobs in the job slot queue/waiting queue/M
		for i in self.job_slot.slot :
			#[[length],[Resource requirement]]
			if i is not None :
				#resource_profile = [i.len , i.resorce_requirement]
				res_slot = self.machine.available_res_slot[i.len] + i.resorce_requirement 
				ob[1].append(res_slot)
		
		for i in range(20 - len(ob[1])):
			res_slot = np.ones([1, 1]) * [0,0]
			ob[1].append(res_slot[0])
		
		# The resource profile of the jobs in the backlog
		# for i in self.job_backlog.backlog :
		# 	if i is not None :
		# 		resource_profile = [i.len , i.resorce_requirement]
		# 		ob[2].append(resource_profile)
				
		return ob
	
	def reset(self) :
		self.seq_idx = 0
		self.curr_time = 0
        # initialize system
		self.machine = Machine(self.pa)
		self.job_slot = JobSlot(self.pa)
		self.job_backlog = JobBacklog(self.pa)
		self.job_record = JobRecord()
		obs = self.observe()
		return obs
	
	def get_reward(self) :
	    reward = 0
		# Reward based on jobs currently running
	    for j in self.machine.running_job :
		    reward += self.pa.penalty / float(j.len)
		# Reward based on job in the waiting queue
	    for j in self.job_slot.slot :
		    if j is not None :
			    reward += self.pa.penalty / float(j.len)
		# Reward based on job in the backlog
	    for j in self.job_backlog.backlog :
		    if j is not None :
			    reward += self.pa.penalty / float(j.len)
	    return reward


class Job :
	def __init__(self , resorce_requirement , job_len , job_id , enter_time) :
		self.id = job_id
		self.resorce_requirement = resorce_requirement
		self.len = job_len
		self.enter_time = enter_time
		self.start_time = -1  # not being allocated
		self.finish_time = -1


class JobSlot :
	def __init__(self , pa) :
		self.slot = [None] * pa.job_wait_queue


class JobBacklog :
	def __init__(self , pa) :
		self.backlog = [None] * pa.backlog_size
		self.curr_size = 0


class JobRecord :
	def __init__(self) :
		self.record = {}


class Machine :
	def __init__(self , pa) :
		self.num_resources = pa.num_resources
		self.time_horizon = pa.time_horizon
		self.res_slot = pa.res_slot
		self.available_res_slot = np.ones((self.time_horizon , self.num_resources)) * self.res_slot
		self.running_job = []
	
	def allocate_job(self , job , curr_time) :
		allocated = False
		for t in range(0 , self.time_horizon - job.len) :
			new_avbl_res = self.available_res_slot[t : t + job.len , :] - job.resorce_requirement
			if np.all(new_avbl_res[:] >= 0) :
				allocated = True
				self.available_res_slot[t : t + job.len , :] = new_avbl_res
				job.start_time = curr_time + t
				job.finish_time = job.start_time + job.len
				self.running_job.append(job)
				assert job.start_time != -1
				assert job.finish_time != -1
				assert job.finish_time > job.start_time
				break
		return allocated
	
	def time_proceed(self , curr_time) :
		self.available_res_slot[:-1 , :] = self.available_res_slot[1 : , :]
		self.available_res_slot[-1 , :] = self.res_slot
		for job in self.running_job :
			if job.finish_time <= curr_time :
				self.running_job.remove(job)


if __name__ == '__main__' :
	print("Unit Test Environment")
	pa = parameters.Parameters()
	pa.job_wait_queue = 5
	pa.simu_len = 50
	pa.num_ex = 10
	pa.new_job_rate = 1
	
	env = Env(pa , job_sequence_len = [3 , 1 , 1 , 1 , 3 , 1 , 2 , 3 , 4 , 5] ,
	          job_sequence_size = [[9 , 2] , [9 , 1] , [2 , 8] , [8 , 2] , [7 , 1] , [2 , 10] , [1 , 10] , [2 , 7] ,
	                               [4 , 8] , [2 , 9]])
	
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	env.step(5)
	
	print("Jobs are now in job slot and job backlog")
	
	ob , reward , done , info = env.step(0)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)
	ob , reward , done , info = env.step(1)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)
	ob , reward , done , info = env.step(2)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)
	ob , reward , done , info = env.step(3)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)
	ob , reward , done , info = env.step(4)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)
	ob , reward , done , info = env.step(4)
	print("Jobs in waiting queue (M): " , ob[1] , "\n Reward: " , reward , "\n Done: " , done)