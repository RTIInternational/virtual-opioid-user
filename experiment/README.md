# Counterfeit Pills Analysis

This experiment studies the effect of counterfeit pills on several outcomes, principally the likelihood of overdose.

## Experiment Design

We hypothesize that an increase in the prevalence of counterfeit pills will lead to a higher risk of overdose and a higher likelihood that people using pills will increase their preferred dose.

- Independent variables:
    - `counterfeit_prob`: the probability that any given dose will consist of counterfeit pills. This could reflect changes in the supply and/or changes in user behavior.
    - `dose_variability`: the maximum proportion by which a dose consisting of counterfeit pills may vary from the intended dose.
    - `fentanyl_prob`: the probability that a dose consisting of counterfeit pills will be adulterated with fentanyl. This causes the counterfeit dose to be higher than the intended dose by another multiplier.

- Dependent variables:
    - `dose_increase`: the amount by which the user's preferred dose increases from the start of the simulation to the end
    - `overdoses`: the number of time the user overdoses during the simulation

The principal mechanism of the experiment is to sweep through a range of counterfeit pill prevalences and record the outcomes. The relationship between counterfeit pill prevalence and the dependent variables is mediated by dose variability and fentanyl probability. Therefore, we also sweep through dose variability and fentanyl probability values at each value of counterfeit pill prevalence. 

The relationship may also be mediated or moderated by several other VOU parameters which are not directly related to counterfeit pills. Therefore, we randomize the values of the following parameters over repeated runs for each scenario. (Specific mechanism TBD)
- `availability`
- `starting_dose`
- `dose_increase`
- `behavioral_variability`
- `external_risk`
- `internal_risk`

## Scenarios

The scenarios which make up the experiment are defined in `experiment_params.json` (`IV_Levels`). At each value of `counterfeit_prob` a scenario is created for all combinations of `dose_variability` and `fentanyl_prob`. 

### Other parameters/covariates

The other VOU parameters (listed above) are currently set according to the `user_types` defined in `experiment_params.json`. For each combination of `counterfeit_prob`, `dose_variability`, and `fentanyl_prob`, a batch of simulations is run for each user type.

This approach was problematic, because the user type overdetermined the likelihood of overdose to the extent that effects of counterfeit pill prevalence were difficult to discern. Future versions of the experiment will incorporate more variability in the other VOU parameters to resolve this issue.

## Running the experiment

1. Create a new virtual environment
1. Install the VOU package with `pip install -e .`
1. Install VOU dependencies with `pip install -r requirements.txt`
1. Install experiment-specific dependencies with `pip install -r experiment/requirements.txt`
1. Prepare the `scenarios` directory by running `python experiment/prepare.py`
    - This step creates a directory for each scenario defined in `experiment_params.json`.
    - Each scenario directory contains a parameters file which will define the batch simulation for that scenario.
    - Command line arguments can be used to vary the random seed and number of iterations. E.g. `python experiment/prepare.py --seed=123 --n_iterations=10`.
1. Run the experiment by running `python experiment/run.py`
    - This step runs a batch experiment for each scenario directory using the list of seeds in `scenarios/seeds.txt`. 
    - It saves results for each batch in the scenario directories.
1. Analyze the results with `experiment/analyze.ipynb`
    - NOTE: `experiment/analyze.py` is currently incomplete.
