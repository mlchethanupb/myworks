#
# <aicon> build script.
#

.PHONY: all

#.PHONY: default test install uninstall clean realclean

# Make file for Scheduling Project
	
SHELL=/bin/bash
CONDAROOT = ~/miniconda3/bin/conda
prefix_discrete = Discrete_DeepRM/
prefix_multibinary = MultiBinary_DeepRM/

application_update:
	sudo apt-get update
	sudo apt-get install python-numpy python-scipy python-dev python-pip python-nose g++ libopenblas-dev git
	sudo apt-get install python-matplotlib

install_miniconda:
	@echo 'installing miniconda 3 '
	mkdir -p ~/miniconda3
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
	bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
	rm -rf ~/miniconda3/miniconda.sh
	~/miniconda3/bin/conda init bash
	~/miniconda3/bin/conda init zsh
	@echo 'installtion done Please restart your shell'

upgrade_miniconda:
	@echo 'updating the miniconda with the required prerequisites'
	~/miniconda3/bin/conda install python=3.7.6
	~/miniconda3/bin/conda install tensorflow=1.15 
	~/miniconda3/bin/conda install -c anaconda mpi4py 
	~/miniconda3/bin/conda install pytorch torchvision -c pytorch	
	@echo 'Done'	
	
pip_files:
	pip install gym
	pip install numpy --upgrade	
	pip install stable-baselines
	pip install SQLAlchemy
	pip install -e .
	
raytune:
	pip install ax-platform 
	pip install ray
	pip install ray[rllib]
	pip install cmake
	pip install cython 
	pip install git+https://github.com/cornellius-gp/gpytorch.git 
	pip install git+https://github.com/pytorch/botorch.git

lasagne_theano:
	pip install lasagne==0.1
	pip install -I theano==0.7

clean:
	@echo 'cleaning up temporary files'
	find . -name '*.pyc' -type f -exec rm {} ';'
	find . -name '__pycache__' -type d -print | xargs rm -rf
	@echo 'NOTE: you should clean up the following occasionally (by hand)'
	git clean -fdn


#Phase - I

run-script:
	python3 run.py
	python3 Script.py

run-stableBaseLine_Models_Training:
	python3 stableBaseLine_Models_Training.py
	
run-raytune:
	python3 raytuneAllAgents.py
   
loadvariation:
	python3 LoadVariation.py
	python3 loadVariationDiscrete.py

train-models:
	python3 Train_all.py

run-withholdjobs:
	python3 Withhold_Jobs.py

run-job-tradeoff:
	python3 Joblength_Tradeoff.py

#Phase - II
# Discrete Environment 

run-train:
	python3 $(prefix_discrete)train.py

run-raytune_discrete:
	python3 $(prefix_discrete)raytune_discrete.py

run-load_Variation_json:
	python3 $(prefix_discrete)load_Variation_json.py

run-load_Variation_Discrete:
	python3 $(prefix_discrete)load_Variation_Discrete.py

run-run:
	python3 $(prefix_discrete)run.py

run-Withheld_Jobs_Discrete:
	python3 $(prefix_discrete)Withheld_Jobs_Discrete.py

run-job_generation:
	python3 $(prefix_discrete)job_generation.py


#Multibinary 

run-Train_all:
	python3 $(prefix_multibinary)Train_all.py

run-LoadVariation:
	python3 $(prefix_multibinary)LoadVariation.py

run-Script:
	python3 $(prefix_multibinary)Script.py

run-Withhold_Jobs:
	python3 $(prefix_multibinary)Withhold_Jobs.py
