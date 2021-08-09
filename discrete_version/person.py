import sys
from enum import IntEnum, unique


@unique
class PersonUseState(IntEnum):
    NON_USER = 0
    USER = 1
    DEPENDENT = 2
    OUD_MILD = 3
    OUD_MODERATE = 4
    OUD_SEVERE = 5

    def __str__(self):
        return self.name


class Person:
    def __init__(self, rng, opioid):
        self.rng = rng
        self.opioid = opioid
        self.use_state = PersonUseState.NON_USER
        self.become_user_day = None
        self.dose_increase_day = None
        self.progress_use_state_day = None

        # Attributes to store the person's history over time:
        self.used_opioids = {}
        self.opioid_dose = {}
        self.use_state_over_time = {}
        self.overdosed = []
        self.died = None

        # ------
        # Each person is assigned several values upon instantiation:
        # ------
        #
        # 1. The risk multiplier affects their likelihood to become a user, become an
        # addict, and increase their dose once using. This is intended to represent the
        # person's social, environmental, and demographic risk factors in composite. It
        # will eventually be replaced with a formula based on actual variables.
        self.risk_multiplier = self.rng.uniform(1, 2)

        # 2. The risk tolerance value affects their likelihood to become a user, increase
        # their dose, and decrease their dose after overdosing. This is intended to
        # represent the person's psychological predisposition to take risks.
        self.risk_tolerance = self.rng.uniform(1, 2)

        # 3. The use probabilities determine the person's probability of using opioids
        # each day after using for the first time. Nondependent use probability applies
        # before the person becomes dependent. It is a random variable scaled by the
        # person's risk multiplier and risk aversion. Dependent use probability applies
        # after the person becomes dependent. It is a product of their nondepended use
        # probabiltiy with some noise introduced.
        base = self.rng.uniform(0.005, 0.1)
        self.nondependent_use_prob = base * self.risk_multiplier * self.risk_tolerance

        # We scale the person's nondependent use probability such that the lowest possible
        # value (0.005) will equate to a dependent use probability of 0.5, and the highest
        # possible value (0.4) will equate to a dependent use probability of 1.
        #
        # These values are generated by solving for the following system of equations:
        # 0.005a + b = 0.5
        # 0.4a + = 1
        #
        # We then scale the value with random noise.
        a = 100 / 79
        b = 39 / 79
        noise = self.rng.uniform(0.9, 1.1)
        self.dependent_use_prob = ((self.nondependent_use_prob * a) + b) * noise
        if self.dependent_use_prob > 1:
            self.dependent_use_prob = 1

        # Each person's current dose starts out at the lowest possible dose and can
        # increase over time. For now, we assume each person starts with
        # a dose of 10 mg.
        self.current_dose_index = 0
        self.current_dose = self.opioid.doses[self.current_dose_index]

    def set_become_user_day(self):
        """
        Randomly set the day on which the person will first use opioids.
        """
        # First, choose the baseline day the person will first use opioids. This is
        # drawn from a triangular distribution with the lower limit 15 years old,
        # the mode 20 years old, and the upper limit 40 years old.
        lower_limit = 15 * 365
        mode = 20 * 365
        upper_limit = 40 * 365
        days = self.rng.triangular(lower_limit, mode, upper_limit)

        # Next, adjust the baseline days by the person's risk multiplier and risk tolerance.
        risk_adjusted_days = (
            days * (1 / self.risk_multiplier) * (1 / self.risk_tolerance)
        )

        # If the risk-adusted days is below the lower limit, reset to the lower limit.
        if risk_adjusted_days < lower_limit:
            risk_adjusted_days = lower_limit

        return int(risk_adjusted_days)

    def days_to_next_use_state(self):
        """
        Randomly set the number of days until the person experiences onset of the
        next stage of opioid use disorder.
        """
        # First, determine which state the person is currently in, and set the scale
        # parameter for the Weibull distribution from which their time to next
        # state will be drawn.
        if self.use_state == PersonUseState.USER:
            # For progression from use to dependence, the Weibull distribution scale
            # parameter is equivalent to three years.
            alpha = 3 * 365
        elif self.use_state in [
            PersonUseState.DEPENDENT,
            PersonUseState.OUD_MILD,
            PersonUseState.OUD_MODERATE,
        ]:
            # For progression through the stages of clinical OUD, the scale parameter
            # is equivalent to two years.
            alpha = 2 * 365
        else:
            raise ValueError("Unexpected use state to generate days to next state.")

        # Choose the baseline number of days before the person becomes dependent.
        # This is drawn from a Weibull distribution with shape parameter (beta) of 2.5.
        beta = 2.5
        days = self.rng.weibullvariate(alpha, beta)

        # Next, adjust the baseline number of days by the person's risk multiplier.
        risk_adjusted_days = (
            days * (1 / self.risk_multiplier) * (1 / self.risk_tolerance)
        )
        return int(risk_adjusted_days)

    def take_opioid(self, day):
        """
        Check whether opioid is available. If so, take opioids. Add values to attributes
        indicating opioid consumption on specified day. Then check whether person overdosed. 
        """
        if self.opioid.is_available:
            self.used_opioids[day] = 1
            if day in self.opioid_dose:
                self.opioid_dose[day] += self.current_dose
            else:
                self.opioid_dose[day] = self.current_dose

            # Also update use state over time to keep track of the person's current state
            # at the time of taking opioid.
            self.use_state_over_time[day] = self.use_state.__str__()

            # Check if the person overdosed
            rand = self.rng.random()
            if rand < self.opioid.overdose_probability[self.current_dose_index]:
                self.overdose(day)

    def overdose(self, day):
        """
        Add value to person attribute indicating overdose on specified day. Then check
        whether the person died.
        """
        self.overdosed.append(day)

        # Check if the person died. Per Dunn et al 2010, about 1 in every 8.5 ODs is
        # fatal.
        rand = self.rng.random()
        if rand < (1 / 8.5):
            self.died = day
            sys.exit(f"Person had a fatal overdose at day {day}")

        # If the person survived, check whether they will reduce their dose in response
        # to the overdose. This depends on their risk tolerance.
        if self.rng.uniform(1, 2) > self.risk_tolerance:
            if self.current_dose_index == 0:
                pass
            elif self.current_dose_index <= 4:
                self.current_dose_index -= 1
            else:
                self.current_dose_index -= 2
            self.current_dose = self.opioid.doses[self.current_dose_index]
            # Reschedule the next dose increase.
            self.dose_increase_day = day + self.days_to_increase_dose()

    def days_to_increase_dose(self):
        """
        Schedule the time until person will next increase their opioid dose.
        """
        # Get base lambda parameter for exponential distribution from which time to dose
        # increase is drawn. This depends on the person's current dose.
        base_lambda = self.opioid.dose_increase_lambda[self.current_dose]

        # Adjust base lambda parameter for the person's current use state. The base
        # values are for a person with severe OUD. Less severe use states lead to more
        # time before increasing the dose.
        if self.use_state == PersonUseState.OUD_MODERATE:
            adjusted_lambda = base_lambda / 2
        elif self.use_state == PersonUseState.OUD_MILD:
            adjusted_lambda = base_lambda / 4
        elif self.use_state == PersonUseState.DEPENDENT:
            adjusted_lambda = base_lambda / 8
        elif self.use_state == PersonUseState.USER:
            adjusted_lambda = base_lambda / 16
        else:
            adjusted_lambda = base_lambda

        # Calculate days until next dose based on adjusted lambda and the person's
        # risk multiplier.
        days = self.rng.expovariate(adjusted_lambda)
        risk_adjusted_days = days * (1 / self.risk_multiplier)
        return int(risk_adjusted_days)

    def increase_dose(self):
        """
        Increase the current dose.
        """
        self.current_dose_index += 1
        self.current_dose = self.opioid.doses[self.current_dose_index]

    def progress_use_state(self):
        """
        Move to the next use state
        """
        self.use_state = PersonUseState(self.use_state.value + 1)