from collections import deque
from enum import IntEnum, unique
from itertools import repeat
from random import Random

import numpy as np

from vou.utils import load_json, logistic, weighted_random_by_dct


@unique
class BehaviorWhenResumingUse(IntEnum):
    SAME_DOSE = 0
    LOWER_DOSE = 1


@unique
class OverdoseType(IntEnum):
    NON_FATAL = 0
    FATAL = 1


@unique
class DoseIncreaseSource(IntEnum):
    PRIMARY_DOCTOR = 0
    SECONDARY_DOCTOR = 1
    DEALER = 2
    WILL_NOT_INCREASE = 3
    FIRST_ATTEMPT = 4


class Person:
    def __init__(
        self,
        rng: Random,
        starting_dose: int = 50,
        dose_increase: int = 25,
        base_threshold: float = 0.001,
        tolerance_window: int = 3_000,
        external_risk: float = 0.5,
        internal_risk: float = 0.5,
        behavioral_variability: float = 0.1,
        behavior_when_resuming_use: BehaviorWhenResumingUse = None,
    ):
        # Parameters
        self.rng = rng
        self.starting_dose = starting_dose
        self.dose = starting_dose
        self.dose_increase = dose_increase
        self.threshold = base_threshold
        self.tolerance_window = tolerance_window
        self.external_risk = external_risk
        self.internal_risk = internal_risk
        self.behavioral_variability = behavioral_variability
        self.update_downward_pressure()
        self.set_risk_logit()
        self.behavior_when_resuming_use = behavior_when_resuming_use
        self.post_OD_use_pause = None
        self.last_dose_increase = 0

        self.drug_params = load_json("vou/drug_params.json")

        # A bunch of empty lists to store data during simulation
        self.concentration = []
        self.tolerance_input = deque(repeat(0, self.tolerance_window))
        self.tolerance_input_sum = 0
        self.desperation = []
        self.habit = []
        self.effect = []
        self.overdoses = []
        self.effect_record = {}
        self.dose_peaks = []
        self.dose_increase_record = {}

    def update_downward_pressure(
        self, midpoint_min: int = 100, midpoint_max: int = 1_000
    ):
        """
        Sets the person's downward pressure. Downward pressure is intended to represent
        the person's overall motivation NOT to use and increase dose. It counterbalances
        their motivation TO use from their threshold and desperation and their motivation
        TO increase dose from their effect and increase threshold.

        Downward pressure is computed with a logistic function taking the following
        arguments:

        - Person's external risk: used as the intercept, or "baseline" downward pressure
        - Person's internal risk: transformed and used as the midpoint of the logistic
          curve
        - Person's current dose: used as the X value
        """
        # Person's internal risk is a value from 0 to 1. We use this in its raw
        # form, but also need to convert it to the sigmoid midpoint parameter for the
        # downward pressure logistic function. This function takes an internal risk from
        # 0 to 1 and scales it to a midpoint in the specified range.
        midpoint_range = midpoint_max - midpoint_min
        midpoint = (self.internal_risk * midpoint_range) + midpoint_min

        # External risk is quantified as 0=good, 1=bad for intuitiveness. However,
        # in the logistic function for downward pressure, 0 is bad and 1 is good,
        # since higher values lead to more downward pressure. Therefore, we invert
        # external risk to get the user's downward pressure baseline.
        baseline_dp = 1 - self.external_risk

        # Main logistic function
        self.downward_pressure = baseline_dp + (
            (1 - baseline_dp) / (1 + np.exp(-0.005 * (self.dose - midpoint)))
        )

    def set_risk_logit(self):
        """
        The risk logit is used to adjust the person's threshold for opioid use. Persons 
        with extreme risk levels (low or high) will have extreme threshold multipliers,
        while persons with normal risk levels will have threshold multipliers close to zero. 
        """
        avg_risk = (self.external_risk + self.internal_risk) / 2
        self.risk_logit = np.log(avg_risk / (1 - avg_risk)) / 0.25

    def lower_dose_after_pause(self):
        """
        Sets the person's dose to their maximum past habit, rounded to the nearest
        increment of their dose increase amount.
        Also updates their downward pressure since dose has changed.
        """
        self.dose = self.dose_increase * round(max(self.habit) / self.dose_increase)
        self.update_downward_pressure()

    def will_take_dose(self, t: int):
        """
        Evaluates several conditions to decide whether the person will take another
        dose at a given time point.

        Returns a boolean value indicating whether the person will take a dose.
        """
        # Is a recent overdose preventing the person from using?
        if self.overdoses and t < self.overdoses[-1] + self.post_OD_use_pause:
            return False
        # Does the person want another dose?
        elif self.concentration[-1] > self.threshold:
            return False
        # Does downward pressure prevent person from taking dose when they want one?
        elif self.rng.random() < self.downward_pressure:
            return False
        else:
            return True

    def did_overdose(self, x0: float = 1243.6936832876, k: float = 0.0143710866):
        """
        Checks whether the person's most recent opioid dose causes an overdose.

        First, a baseline OD risk value is generated using a function derived from
        Dasgupta et al 2016. A logistic model was fitted to their data, along with 
        the assumption that a dose of 2 grams has an OD probability of 1. (See
        notebooks/od_risk_curve.ipynb). We use that model to generate the baseline
        risk value for the person's dose.

        Since the Dasgupta study used prescription data, we assume that these overdose
        risks are for people who are tolerant to their prescribed dose. Therefore,
        we add an additional risk multiplier based on the ratio of the dose to the
        person's tolerance.

        A very general heuristic is that at steady state, (preferred_dose / tolerance)
        roughly equals 2. We define "excess" as (dose / tolerance) - 1, or roughly 1 at
        steady state. We multiply the person's baseline OD risk by this excess squared.
        """
        # Use the second-to-last values of concentration and habit, since this method
        # is designed to be invoked when a dose peak has been detected. The peak finding
        # logic detects peaks at the time step *after* the peak occurred, so the peak
        # values are one item back in these lists.
        dose = self.concentration[-2]
        tolerance = self.habit[-2]

        # bound extremely low tolerance values to avoid huge excess values
        tolerance = max(1, tolerance)

        # parameters based on Dasgupta et al 2016 - see notebooks/od_risk_curve.ipynb
        baseline_OD_risk = logistic(x=dose, L=1, k=k, x0=x0)

        excess = ((dose / tolerance) - 1) ** 2

        tolerance_adjusted_OD_risk = baseline_OD_risk * excess

        if self.rng.random() < tolerance_adjusted_OD_risk:
            # Overdose occurred
            return True

    def overdose(self, t: int):
        """
        Takes the necessary actions when the person has overdosed. Records the OD,
        sets the amount of time the person will stop using after OD, and adjusts
        their dose if they will reduce their dose after OD.

        Returns the type of overdose, fatal or non-fatal. Simulation.simulate() uses
        this value to break the simulation loop in the case of a fatal OD.
        """
        self.overdoses.append(t)
        # Set amount of time person will stop using after OD.
        self.post_OD_use_pause = self.compute_OD_use_pause()
        # Adjust person's dose.
        self.dose = self.dose * self.compute_OD_dose_reduction()
        # Check if overdose caused death. Per Dunn et al 2010, about 1 in every 8.5
        # ODs is fatal.
        if self.rng.random() < (1 / 8.5):
            return OverdoseType.FATAL
        else:
            return OverdoseType.NON_FATAL

    def compute_OD_use_pause(self):
        """
        Computes the amount of time the person will pause use after an overdose based
        on the person's risk factors and a random draw. The lowest risk persons will
        pause 60 days. This value decays exponentially quite quickly, since research
        shows that most persons resume use within 24 hours of an OD.
        """
        maximum = 60 * 100
        rate = -0.999
        rand = self.rng.uniform(0.5, 1.5)
        combined_risk = self.internal_risk + self.external_risk
        pause = (maximum * (1 + rate) ** combined_risk) * rand
        return pause

    def compute_OD_dose_reduction(self):
        """
        Computes a multiplier by which the person will reduce their dose after an OD
        based on the person's risk factors and a random draw. The lowest risk persons
        will reduce their dose by half, while the highest risk persons will maintain
        the same dose.
        """
        intercept = 0.5
        slope = 0.25
        rand = self.rng.uniform(0.5, 1.5)
        combined_risk = self.internal_risk + self.external_risk
        dose_reduction = (combined_risk * slope + intercept) * rand
        if dose_reduction > 1:
            return 1
        else:
            return dose_reduction

    def will_increase_dose(
        self, effect_window: int = 20, increase_threshold: float = 0.4,
    ):
        """
        Checks whether the person will increase their dose. Based on a comparison of
        the average of past dose effects to the person's desired dose. Effect window
        and increase threshold are calibrated parameters and not intended to be varied
        during simulation.

        Logic for the source of the increased dose is added here.  If a person will increase
        their dose for the first time, they will attempt through their primary doctor.  If
        this is their second time, they will have a 50% chance of trying through a secondary
        doctor or a dealer.
        """
        self.source_probability_primary = self.drug_params["source_probability"][
            "initial_doctor_increase"
        ]
        self.source_probability_secondary = self.drug_params["source_probability"][
            "secondary_doctor"
        ]
        self.source_probability_dealer = self.drug_params["source_probability"][
            "dealer"
        ]
        self.secondary_doc_dealer_prob = self.drug_params["secondary_doc_dealer_prob"]

        if len(list(self.dose_increase_record.values())) == 0:
            last_attempt_src = DoseIncreaseSource.PRIMARY_DOCTOR
            last_attempt_success = None

        else:
            last_attempt_src = list(self.dose_increase_record.values())[-1]["source"]
            last_attempt_success = list(self.dose_increase_record.values())[-1][
                "success"
            ]

        last_n_dose_effects = [
            self.effect_record[d]
            for d in self.dose_peaks[-effect_window:]
            if d > self.last_dose_increase
        ]

        # Check if individual will increase dose
        if self.dose >= 2_000:

            will_increase_dose = False
            increase_dose_src = DoseIncreaseSource.WILL_NOT_INCREASE

        elif len(last_n_dose_effects) == 0:

            will_increase_dose = False
            increase_dose_src = DoseIncreaseSource.WILL_NOT_INCREASE

        elif np.mean(last_n_dose_effects) >= (self.dose * increase_threshold):

            will_increase_dose = False
            increase_dose_src = DoseIncreaseSource.WILL_NOT_INCREASE

        elif self.rng.random() <= self.downward_pressure:

            will_increase_dose = False
            increase_dose_src = DoseIncreaseSource.WILL_NOT_INCREASE
        else:
            will_increase_dose = True

        # Determine source of dose increase
        if will_increase_dose == True:

            # if first time trying to increase dose, go to primary doctor for potential increase
            ## Also, if the last attempt to increase from primary was successful, try again with primary
            if (len(self.dose_increase_record) == 0) | (
                (last_attempt_src == DoseIncreaseSource.PRIMARY_DOCTOR)
                & (last_attempt_success == True)
            ):

                # probability of primary doctor increasing
                if self.rng.random() <= self.source_probability_primary:
                    will_increase_dose = True
                    increase_dose_src = DoseIncreaseSource.PRIMARY_DOCTOR

                else:
                    will_increase_dose = False
                    increase_dose_src = DoseIncreaseSource.PRIMARY_DOCTOR

            # if the last time they tried to increase, they tried from their primary and failed, try from either dealer or secondary doctor

            ##### If your last increase attempt was successful, but it was a secondary doctor, you'll enter this situation again
            elif (last_attempt_success == False) | (
                last_attempt_src == DoseIncreaseSource.SECONDARY_DOCTOR
            ):

                if self.rng.random() <= self.secondary_doc_dealer_prob:

                    if self.rng.random() <= self.source_probability_secondary:
                        will_increase_dose = True
                        increase_dose_src = DoseIncreaseSource.SECONDARY_DOCTOR

                    else:
                        will_increase_dose = False
                        increase_dose_src = DoseIncreaseSource.SECONDARY_DOCTOR

                else:

                    if self.rng.random() <= self.source_probability_dealer:
                        will_increase_dose = True
                        increase_dose_src = DoseIncreaseSource.DEALER

                    else:
                        will_increase_dose = True
                        increase_dose_src = DoseIncreaseSource.DEALER

            else:  # only other option is you successfuly found a dealer, in which case you can always increase

                will_increase_dose = True
                increase_dose_src = DoseIncreaseSource.DEALER

        # If first timestep then source is primary doctor
        if len(self.dose_increase_record) == 0:  # if it's first timestep
            increase_dose_src = DoseIncreaseSource.PRIMARY_DOCTOR

        # if not first timestep then source is the last source that doesn't equal WILL_NOT_INCREASE
        elif increase_dose_src == DoseIncreaseSource.WILL_NOT_INCREASE:
            increase_dose_src = [
                x
                for x in list(self.dose_increase_record.values())
                if x["source"] != DoseIncreaseSource.WILL_NOT_INCREASE
            ][-1]["source"]

        # Dose type based on dose source
        increase_dose_type = weighted_random_by_dct(
            self.drug_params["drugs_by_source"][str(increase_dose_src)], self.rng
        )

        return {
            "source": increase_dose_src,
            "success": will_increase_dose,
            "dose_type": increase_dose_type,
        }

    def increase_dose(self, t: int):
        """
        Takes the necessary steps when the person increases their dose. Updates dose,
        records the current time as the last time of dose increase, and updates the
        person's downward pressure for the new dose.
        """
        self.dose += self.dose_increase
        self.last_dose_increase = t
        self.update_downward_pressure()
