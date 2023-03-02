import math
from random import Random

import numpy as np

from vou.person import BehaviorWhenResumingUse, DoseIncreaseSource, OverdoseType, Person
from vou.utils import logistic, weighted_random_by_dct


class Simulation:
    def __init__(
        self,
        person: Person,
        rng: Random,
        days: int = 730,
        stop_use_day: int = None,
        resume_use_day: int = None,
        dose_variability: float = 0.1,
        availability: float = 0.9,
        bad_batch_prob: float = 0.0001,
        counterfeit_prob: float = 0.1,
        source_variability: float = 0.2,
        fentanyl_variability: float = 0.1,
    ):
        # Parameters
        self.person = person
        self.rng = rng
        self.days = days
        self.stop_use_time = None if stop_use_day is None else stop_use_day * 100
        self.resume_use_time = None if resume_use_day is None else resume_use_day * 100
        self.dose_variability = dose_variability
        self.availability = availability
        self.bad_batch_prob = bad_batch_prob
        self.counterfeit_prob = counterfeit_prob
        self.source_variability = source_variability
        self.fentanyl_variability = fentanyl_variability

        # Variables used in simulation
        self.time_since_dose = 0
        self.last_amount_taken = 0
        self.conc_when_dose_taken = 0
        self.dose_peak_pending = False
        self.opioid_available = True
        self.integralA = [0]
        self.integralB = [0]
        self.integralC = [0]
        self.integralD = [0]
        self.dose_method = "Pill"
        self.dose_source = DoseIncreaseSource.PRIMARY_DOCTOR
        self.compliant = True

    def simulate(self):
        """
        The main function to conduct a simulation. Simulates the opioid use behavior of a
        single person. The simulation loops through time points (100 time points per day,
        ~15 minutes each) for the number of days specified at instantiation. Conducts
        several steps at each time point to simulate the person's opioid use behavior.
        Records the key measures (opioid concentration, habit, effect, desperation, and
        overdoses) over time.
        """
        for t in range(self.days * 100):

            # Reset dose taken indicator for next iteration
            dose_taken_at_t = False

            # Add to time since last dose
            self.time_since_dose += 1

            # Compute the person's concentration of opioid using pharmacokinetic model
            conc = self.compute_concentration()
            self.person.concentration.append(conc)

            # Add concentration to tolerance input
            self.person.tolerance_input_sum -= self.person.tolerance_input.popleft()
            self.person.tolerance_input_sum += conc
            self.person.tolerance_input.append(conc)

            # Update opioid availability
            self.update_availability(t)

            # Check if the person will take another dose
            if self.opioid_available is True:
                # if self.person.will_take_dose(t) is True:
                if self.person.will_take_dose(t) is True or t % 100 == 0:
                    self.record_dose_taken(t)
                    dose_taken_at_t = True

            # Compute the person's opioid use habit at t
            self.person.habit.append(self.compute_habit(t))

            # Compute the opioid's effect on the person (concentration - habit)
            self.person.effect.append(self.compute_effect())

            # If peak concentration for the last dose taken has not been reached
            # yet, check if it was reached at this time step
            if (
                self.dose_peak_pending is True
                and dose_taken_at_t is False
                and len(self.person.concentration) > 1
            ):
                # If concentration at t is lower than at t-1, then t-1 was the dose's peak.
                # Take all the actions necessary to record the dose peak.
                if self.person.concentration[-1] < self.person.concentration[-2]:
                    # Reset indicator
                    self.dose_peak_pending = False
                    # Check for overdose.
                    if self.person.did_overdose() is True:
                        overdose = self.person.overdose(t)
                        if overdose == OverdoseType.FATAL:
                            break
                    # Store effect in a dict of effects at time of each dose's peak
                    # (to be used in determining when the person increases their dose.)
                    self.person.effect_record[t - 1] = self.person.effect[-2]
                    self.person.dose_peaks.append(t - 1)
                    # Check if the person will increase their dose.
                    dose_increase = self.person.will_increase_dose()
                    if dose_increase["success"]:
                        self.person.increase_dose(t)
                    self.person.dose_increase_record[t] = dose_increase

            # Compute the person's threshold and desperation
            # First, compute integrals of concentration to be used in calculating
            # threshold and desperation
            self.compute_concentration_integrals()
            # Next, compute the person's desperation at t
            self.person.desperation.append(self.compute_desperation())
            # Finally, update the person's threshold for the next iteration
            self.person.threshold = self.compute_threshold()

    def compute_concentration(self, ke: float = 0.0594):
        """
        Computes the person's concentration of opioids in MME at a time step.

        The coefficient of elimination (Ke) was calibrated to the half life of morphine.
        Per Lotsch 2005, 3 studies identifed this value as 2.8 hours, which we use here.

        This model uses 100 time steps per day, so each time step equates to
        24 * 60 / 100 = 14.4 minutes. The half life in model time units is 
        2.8 * 60 / 14.4 = 11.667 time units.

        For first-order decay functions, the decay constant Ke = ln(2) / half_life.
        Therefore, in our case:

        Ke = ln(2) / 11.667 = 0.0594

        The coefficient of absorption (Ka) can be varied to simulate different modes
        of opioid administration. The default value is high enough that the entire dose
        is absorbed by the following time step, simulating an injection (or any mode of
        administration where the entire dose is absorbed within ~15 minutes). Reducing
        Ka can simulate orally consuming pills, where it takes several time steps for the
        dose to be absorbed. See `notebooks/pk_absorb_eliminate.ipynb` for details.
        """
        if self.dose_method == "Pill":
            ka = 0.4
        else:
            ka = 10

        starting_amount = self.conc_when_dose_taken + self.last_amount_taken
        t = self.time_since_dose

        return ((starting_amount * ka) / (ka - ke)) * (
            (math.exp(-ke * t)) - (math.exp(-ka * t))
        )

    def compute_effect(self, ke: float = 0.0594):
        """
        Computes opioid's effect on the the person at a time step, given their
        concentration of opioid and opioid use habit.
        
        Ke is a calibrated parameter and Ka can be adjusted to simulate different modes of
        administration. See docstring for compute_concentration for details.
        """
        if self.dose_method == "Pill":
            ka = 0.4
        else:
            ka = 10

        starting_amount = (
            self.conc_when_dose_taken + self.last_amount_taken - self.person.habit[-1]
        )
        t = self.time_since_dose

        effect = ((starting_amount * ka) / (ka - ke)) * (
            (math.exp(-ke * t)) - (math.exp(-ka * t))
        )

        return max(effect, 0)

    def update_availability(self, t: int):
        """
        Updates the variable indicating whether opioids are available to the user.

        Includes two steps:

        1. Update availability once per day (100 time units) Based on a random draw,
        adjusted by person's desperation, relative to the parameter indicating how often
        opioids are available on any given day.

        2. Check if t is in the stop use period. If so, the drug is always unavailable.
        Further, if t is the time of resuming use after stop, check whether the person
        will reduce their dose.
        """
        # Step 1
        if t % 100 == 0:
            if self.dose_source in [
                DoseIncreaseSource.PRIMARY_DOCTOR,
                DoseIncreaseSource.SECONDARY_DOCTOR,
            ]:
                self.opioid_available = True
            elif self.dose_source == DoseIncreaseSource.DEALER:
                rand = self.rng.random()
                # Adjust availability by desperation - more desperate user seeks drug
                # more aggressively.
                if self.person.desperation:
                    if self.person.desperation[-2] > 1:
                        rand = rand / self.person.desperation[-2]
                if rand < self.availability:
                    self.opioid_available = True
                else:
                    self.opioid_available = False
            else:
                raise ValueError(
                    f"Unexpected value of simulation.dose_source: {self.dose_source}"
                )
        # Step 2
        if self.stop_use_time:
            if self.resume_use_time:
                if t >= self.stop_use_time and t < self.resume_use_time:
                    self.opioid_available = False
                elif t == self.resume_use_time:
                    if (
                        self.person.behavior_when_resuming_use
                        == BehaviorWhenResumingUse.LOWER_DOSE
                    ):
                        self.person.lower_dose_after_pause()
            elif t >= self.stop_use_time:
                self.opioid_available = False

    def record_dose_taken(self, t):
        """
        Takes the necessary actions when the person has taken a dose.

        Increase record is used to update the dose source, type, and method
        * If this is the first timestep, go with Primary and a random drug from that distribution
        * If not, go with the last specified dose type and source --specified from will_increase_dose
            * This will cause the type of dose to change each time increase is True
        * Method of use will change each time a dose is taken based on the probabilities associated
            with drug type
        """

        # create dataframe of dose increases to determine last source
        ## Currently using option 1 - last source is the continued source
        if len(self.person.dose_increase_record) > 0:

            ### Filter to the last entry where the source was not "WILL NOT INCREASE" and the attempt to increase was a success
            ##### If that does not exist then the source/etc. will be based on primary
            successful_dose_increases = [
                x
                for x in list(self.person.dose_increase_record.values())
                if (x["source"] != DoseIncreaseSource.WILL_NOT_INCREASE)
                & (x["success"] == True)
            ]

            # Determine source
            if len(successful_dose_increases) == 0:  # if first record --primary
                self.dose_source = DoseIncreaseSource.PRIMARY_DOCTOR
                self.dose_type = weighted_random_by_dct(
                    self.person.params["drugs_by_source"][str(self.dose_source)],
                    self.rng,
                )

            else:
                self.dose_source = successful_dose_increases[-1]["source"]
                self.dose_type = successful_dose_increases[-1]["dose_type"]

        else:  # if it's the first timestamp go to primary
            self.dose_source = DoseIncreaseSource.PRIMARY_DOCTOR
            self.dose_type = weighted_random_by_dct(
                self.person.params["drugs_by_source"][str(self.dose_source)], self.rng,
            )

        # Determine the method of use based on the drug
        self.dose_method = weighted_random_by_dct(
            self.person.params["admin_mode_distributions"][self.dose_type], self.rng,
        )

        # check if the person is compliant (non-compliant if source != PRIMARY_DOCTOR)
        if self.dose_source == DoseIncreaseSource.PRIMARY_DOCTOR:
            self.compliant = True

        elif self.dose_source != DoseIncreaseSource.PRIMARY_DOCTOR:
            self.compliant = False

        # Update the dose peak pending indicator, which will cue all time steps in the
        # future to check if peak concentration was reached. When peak concentration is
        # reached, this will be set back to false.
        self.dose_peak_pending = True
        # Update the variable storing the person's concentration when the dose was
        # taken to be used for later concentration calculations.
        self.conc_when_dose_taken = self.person.concentration[-1]
        # Reset the time since dose indicator to zero for concentration calculations.
        self.time_since_dose = 0
        # Update the variable storing the last amount taken for concentration calcs.
        self.last_amount_taken = self.compute_amount_taken()
        # Recalculate the person's concentration for this time step
        new_conc = self.compute_concentration()
        self.person.concentration[-1] = new_conc
        # Add the new concentration to the person's tolerance window
        self.person.tolerance_input_sum -= self.person.tolerance_input.pop()
        self.person.tolerance_input_sum += new_conc
        self.person.tolerance_input.append(new_conc)

        # Add the person's dose_source to the list
        self.person.dose_sources.append(self.dose_source)

    def compute_amount_taken(self):
        """
        Computes the amount of opioid taken in MME when the person takes a dose.

        First, checks whether the user decides to vary their dose. 
        
        Next, check whether the dose consists of counterfeit pills. If not, the dose
        taken is the user's preferred dose exactly. If so, the dose taken is modified
        by several multipliers.

        1. The person's behavioral variability parameter represents variation in the dose
        the person intends to take relative to their usual preferred dose.
        
        2. The dose variability parameter represents general variation in the purity
        and consistency of counterfeit pills.

        3. The fentanyl probabiltiy parameter represents the likelihood that a
        counterfeit pill is part of a "bad batch" contaminated with fentanyl. 
        If so, the modified dose is multiplied by a random value:
        1 + a random draw from an exponential distribution with mean 0.25 (the 
        lambd parameter in random.expovariate is 1 divided by the mean).
        """

        # Behavioral Variability based on user traits
        modified_dose = self.person.dose * self.rng.uniform(
            1 - self.person.behavioral_variability,
            1 + self.person.behavioral_variability,
        )

        # Source Variability -- if from a dealer, additional variability modifier

        if self.dose_source == DoseIncreaseSource.DEALER:
            modified_dose = modified_dose * self.rng.uniform(
                1 - self.source_variability, 1 + self.source_variability
            )

        # There are no counterfeit pills unless from a dealer
        if (self.rng.random() < self.counterfeit_prob) & (
            self.dose_source == DoseIncreaseSource.DEALER
        ):

            modified_dose = modified_dose * self.rng.uniform(
                1 - self.dose_variability, 1 + self.dose_variability
            )
            if self.rng.random() < self.bad_batch_prob:
                modified_dose = modified_dose * (1 + self.rng.expovariate(1 / 0.25))

        if self.dose_type == "fentanyl":
            modified_dose = self.rng.uniform(
                1 - self.fentanyl_variability, 1 + self.fentanyl_variability
            )

        return modified_dose

    def compute_habit(
        self,
        t: int,
        conc_multiplier: int = 1.85,
        L1: float = 1.0275,
        L2: float = 0.58,
        K1: float = 0.2,
        K2: float = 0.0002,
        X1: float = 0.175,
    ):
        """
        Computes the person's opioid use "habit" at a time point.

        We conceptualize habit as a function of the person's recent use behavior. When
        a person has been using more, their habit will be higher.

        Parameters were calibrated and are not intended to be varied during simulation.
        They are defined in the comments below.
        """
        # Go ahead and return zero if this is the first time point.
        if t == 0:
            return 0
        # Compute the rolling mean of the person's opioid concentration using their
        # tolerance window.
        #
        # conc_multiplier is a calibrated parameter used to increase the concentration
        # prior to the logistic effect function. Without this increase, effect is too
        # small relative to concentration.
        rolling_concentration = (
            self.person.tolerance_input_sum / self.person.tolerance_window
        ) * conc_multiplier

        # Compute habit based on a logistic function of the rolling concentration.
        #
        # All of the logistic function parameters are adjusted by dose. This results in
        # the relationship between concentration and effect changing at different doses.
        # This results in the behavior where people tend to maintain use of a low dose
        # for a long time, and increase their dose faster as the dose gets higher.
        #
        # L1 and L2 are calibrated parameters used to vary the logistic curve's maximum
        # value exponentially by dose. This makes habit get higher relative to dose as
        # dose increases.
        #
        # K1 and K2 are calibrated parameters used to vary the logistic growth rate
        # linearly by dose. This makes habit grow more slowly as dose increases, moderating
        # the effect of L1 and L2.
        #
        # X1 is a calibrated parameter used to vary the rolling concentration value at the
        # logistic curve's midpoint by dose. This allows us to obtain a similarly-shaped
        # curve at a wide range of doses.
        return logistic(
            x=rolling_concentration,
            L=(self.person.dose ** L1) * L2,
            k=K1 - (self.person.dose * K2),
            x0=self.person.dose * X1,
        )

    def compute_concentration_integrals(
        self,
        ALPHA1=0.99,
        BETA1=1,
        ALPHA2=0.999,
        BETA2=2000,
        ALPHA3=0.9998,
        BETA3=15000,
        ALPHA4=0.99995,
        BETA4=10000,
    ):
        """
        Computes four integrals of the person's opioid concentration at a time point.

        Each integral holds successively longer-term memory about the person's opioid
        use. Integral A decays rapidly after concentration drops, while integral D
        retains memory of past opioid use for over a year. These values are used in
        calculating a person's desperation and threshold. See Georgiy's Virtual Smoker
        white paper for further discussion of the concept.

        Alphas and betas are calibrated parameters and not intended to be varied
        during simulation.
        """
        self.integralA.append(
            ALPHA1 * self.integralA[-1] + BETA1 * self.person.concentration[-1]
        )
        self.integralB.append(ALPHA2 * self.integralB[-1] + self.integralA[-1] / BETA2)
        self.integralC.append(ALPHA3 * self.integralC[-1] + self.integralB[-1] / BETA3)
        self.integralD.append(ALPHA4 * self.integralD[-1] + self.integralC[-1] / BETA4)

    def compute_threshold(
        self, B1=0.001, B2=0.01, B3=0.5,
    ):
        """
        Computes the person's threshold to take another dose for the next time step.
        If concentration is below the threshold, the person wants another dose.

        Threshold is calculated from integrals of concentration (which should be updated
        prior to computing this threshold at each time step). B1-3 are calibrated
        parameters and not intended to be varied during simulation.

        The threshold is then adjusted by the person's risk logit.
        """
        thresh = (B1 * self.integralB[-1] + B2 * self.integralC[-1]) / (
            1 + B3 * self.integralA[-1]
        )
        if -5 < self.person.risk_logit < 5:
            return thresh
        else:
            if self.person.risk_logit < 0:
                return thresh / np.abs(self.person.risk_logit)
            else:
                return thresh * self.person.risk_logit

    def compute_desperation(self):
        """
        Computes the person's desperation at a time step. Desperation influences
        availability, since more desperate people try harder to seek out opioids. It is
        also one of the key measures recorded over time during the simulation.

        Desperation is calculated from the longest-term memory of past use (integral D)
        moderated by the person's threshold, which decays more quickly after stopping use.
        Together, this makes desperation peak rapidly after the person stops using and
        decay over a few days to weeks, replicating the impact of withdrawal and craving.
        """
        return max(
            (
                self.integralD[-1]
                * (self.person.threshold - self.person.concentration[-1])
                / (self.person.concentration[-1] + 1)
            ),
            0,
        )


if __name__ == "__main__":
    person = Person(rng=Random(1),)

    simulation = Simulation(person=person, rng=Random())
    simulation.simulate()

