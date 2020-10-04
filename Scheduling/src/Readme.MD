## Source Code :

To clear all cache contents and to instal the necessary packages like gym, tensorflow etc., which are mentioned in requirements.txt, We have specified various methods in the make file.
For running all the pre-requisites and pacakage installations needed for executing the actual code the below command needs to be exicuted in the terminal,
```
make all
```
If the specified requirements in txt are already installed, those operations will be skipped by the machine.

Once our pre set up is done. We ned to train the agents and save their respective models by running the command mentioned below,
```
make train-models
```
Once the agents is trained , their models will be saved in zip files.For evaluating the performance of various agents and plotting it in bar graph run,
```
make run-script
```
For different loads, we evaluate the results and plot them by following command,
```
make run-load-variation
```
