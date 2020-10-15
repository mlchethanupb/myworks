.PHONY: all

all: clean-pyc clean-build bootstrap

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

bootstrap: 
	sudo apt install python3
	sudo apt install -y python3-pip
	pip3 install --upgrade pip
	pip3 install example --use-feature=2020-resolver --upgrade setuptools
	pip3 install example --use-feature=2020-resolver -U pip
	pip3 install example --use-feature=2020-resolver -r requirements.txt

train-models:
	python3 Train_all.py

run-script:
	python3 Script.py

run-load-variation:
	python3 LoadVariation.py

run-withholdjobs:
	python3 Withhold_Jobs.py

run-job-tradeoff:
	python3 Joblength_Tradeoff.py
