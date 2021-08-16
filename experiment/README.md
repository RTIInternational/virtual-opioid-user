# Virtual Opioid User Experiments

This directory contains the files needed to run a simulation experiment using Virtual Opioid User. 

## Make a new experiment

- In this repo, experiments are separated by branch. 
- To create a new experiment, make a new branch from master. Experiment branch names should include an `exp-` prefix, e.g. `exp-param-sweeps`. 
- All files generated as part of the experiment (source code, inputs, outputs) should be stored in the experiment directory. 
- Don't merge your changes back into master. Keep experiment code in the experiment branch.
- If you need to change any files outside of the experiment directory, those changes should be made in a separate branch and merged into master. For example, if an experiment involves adding a new function to the `Person` class in `vou/person.py`, that change should be made in a separate branch and  merged into master. 

## Running an experiment

1. Check out the branch for the experiment you want to run (experiments are stored as separate branches)    
1. Create and activate a virtual environment for the experiment
1. Install VOU dependencies with `pip install -r requirements.txt`
1. If there are any experiment-specific dependencies, install them with `pip install -r experiment/requirements.txt` (If this file doesn't exist, assume there are no experiment-specific dependencies)
1. Install the VOU package with `pip install -e vou`
1. Follow experiment-specific directions to run the experiment (will be added to this README in experiment branches)
