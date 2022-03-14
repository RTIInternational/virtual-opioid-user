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

Can we get some real-world data on which to base the scenarios?     

Ideally, we'd get counterfeit pill prevalence and overdose rates for a community. 

E.g.:
- get a real world data point for counterfeit pill prevalence
- calibrate the parameters of the experiment to produce the right number of overdoses at that prevalence
- test scenarios of higher and lower prevalence relative to the baseline

If we can't make this work, we can just use expert opinion from Dan to determine which prevalence values to test.

## Calibration

See above - may want to calibrate if we can base scenarios on real-world data.