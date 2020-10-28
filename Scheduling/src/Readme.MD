# How to execute the project DeepRL.

This readme will help helps an ordinary user(non developer) to execute and get the results with a single command.

# Makefile commands

### `make install_miniconda`

This will download and install miniconda 3.

### `make upgrade_miniconda`

Restart your shell and run this command to upgrade all prerequisties for miniconda 3.

### `make pip_files`

This will install all the basic services like gym and the required environments.

### `make raytune`

This will install raytune and required prerequisties.

### `make clean`

This will help clean the cache in the project.

After completing the pre-setup using the above commands, you can execute the following commands to get the results of the discrete action space.

### `make run-script`

This command will run the DeepRl script for generating required graphs.

### `make run-stableBaseLine_Models_Training`

This command will run the training for the DeepRl agents.

### `make run-raytune`

This command will run the hyperparameter optimization.

### `make loadvariation`

This command will generate the graphs for loadvariations.

On the other hand, once the pre-setup is complete, the following commands can be executed to generate results for multiple binary action space.

We need to train the agents and save their respective models by running the command mentioned below,

### `make train-models`

Once the agents is trained , their models will be saved in zip files.For evaluating the performance of various agents and plotting it in bar graph run,

### `make run-script `

For different loads, we evaluate the results and plot them by following command,

### `make loadvariation`

For different job lengths, we check behavior to see if all jobs are the same by following command,

### `make run-withholdjobs`

For different job lengths, we compare the slowdown by following command,

### `make run-job-tradeoff`


Happy Coding :)
