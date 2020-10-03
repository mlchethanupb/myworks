CURRENT_DIR := $(shell pwd)
VENV_NAME?=.venv
PYTHON=${VENV_NAME}/bin/python

.DEFAULT: help
help:
	@echo "prepare-dev - prepare development environment"
	@echo "clean - remove all"
	@echo "clean-pyc - remove all python file artifacts"
	@echo "build - package"

all:	default

default: clean dev-deps deps build

prepare-dev:
	sudo apt-get -y install python3.5 python3-pip
	python3 -m pip install virtualenv
	make venv

venv:	$(VENV_NAME)/bin/activate 
$(VENV_NAME)/bin/activate: requirements.txt
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	make deps
	touch $(VENV_NAME)/bin/activate

clean:	clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

clean-test:
#	rm -fr 

dev-deps:
	sudo apt-get install python-pip

deps:	#venv
	pip install -U pip 
	pip install -U -r $(CURRENT_DIR)/requirements.txt
	echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

build:	clean

train-models:
	python Train_all.py

run-script:
	python Script.py

run-load-variation:
	python LoadVariation.py