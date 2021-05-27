from vou.person import PersonUseState


class Timer:
    def __init__(
        self, person, rng, run_days: int,
    ):
        self.person = person
        self.rng = rng
        self.run_days = run_days
        self.day = 0

    def simulate(self):
        """
        Runs through a full simulated lifespan of the person. 
        """
        self.start()
        while self.day <= self.run_days:
            self.time_step()

    def start(self):
        """
        Determine when the person starts using opioids and initiate their first dose.
        Progress their use state to USER, schedule their next use state progression,
        and schedule their first dose increase.
        """
        # Draw the day the person will first use opioids.
        self.person.become_user_day = self.person.set_become_user_day()
        # Take opioids on that day.
        self.day = self.person.become_user_day
        self.person.take_opioid(day=self.day)
        # Now that the person has used opioids, progress their use state from non-user to user.
        if self.person.use_state == PersonUseState.NON_USER:
            self.person.progress_use_state()
        else:
            raise ValueError(
                f"Unexpected use state {self.person.use_state}. This function should not only be called at the start of a person's lifespan."
            )
        # Determine the time of the person's first dose increase by adding the number
        # of days until dose increase to the day of first use.
        self.person.dose_increase_day = self.day + self.person.days_to_increase_dose()
        # Determine the time the person will progress to the next use state by adding
        # the number of days until the next use state onset to the day of first use.
        self.person.progress_use_state_day = (
            self.day + self.person.days_to_next_use_state()
        )

    def time_step(self, prob_availability_update: float = 1 / 7):
        """
        Conduct all the necessary steps to simulate one day in the person's lifespan
        of opioid use. 
        """
        # Increment time by one day.
        self.day += 1
        # Before taking opioids, check if the person is scheduled to increase their
        # dose on the current day. If so, increase their dose and schedule the next
        # dose increase.
        self.check_for_dose_increase()
        # Before taking opioids, check if the person is scheduled to progress to the
        # next use state on the current day. If so, progress the state and schedule
        # the next progression.
        self.check_for_use_state_progression()
        # Randomly decide whether to update opioid availability on this day. Default
        # value assumes opioids will become available/not available about once a week.
        if prob_availability_update < 0 or prob_availability_update > 1:
            raise ValueError(
                f"Probability of update {prob_availability_update} outside bounds of 0 and 1."
            )
        if self.rng.random() < prob_availability_update:
            self.person.opioid.update_availability()
        # Determine the person's opioid use for the current day and trigger the person
        # to take determined opioids.
        self.determine_opioid_use()

    def check_for_dose_increase(self):
        """
        Check if the person is scheduled to increase their dose on the current day,
        If so, increase their dose and schedule the next dose increase.
        """
        if self.person.dose_increase_day == self.day:
            # Cannot increase if person is already at maximum dose
            if self.person.current_dose < self.person.opioid.doses[-1]:
                self.person.increase_dose()
                # If this increase did not put the person at the maximum dose, schedule
                # the next dose increase.
                if self.person.current_dose < self.person.opioid.doses[-1]:
                    self.person.dose_increase_day += self.person.days_to_increase_dose()

    def check_for_use_state_progression(self):
        """
        Check if the person is scheduled to progress to the next use state on the
        current day. If so, progress the state and schedule the next progression.
        """
        if self.person.progress_use_state_day == self.day:
            # Cannot progress if person is already in maximum state.
            if self.person.use_state != PersonUseState.OUD_SEVERE:
                self.person.progress_use_state()
                # If this increase did not put the person at the maximum state, schedule
                # the next use state progression.
                if self.person.use_state != PersonUseState.OUD_SEVERE:
                    self.person.progress_use_state_day += (
                        self.person.days_to_next_use_state()
                    )

    def determine_opioid_use(self):
        """
        Determine if and how much the person should take opioids on the current day.
        Dependent on their use state.
        """
        if self.person.use_state == PersonUseState.USER:
            # In the user state, the person takes opioids if a random draw is below their
            # nondependent use probability.
            if self.rng.random() < self.person.nondependent_use_prob:
                self.person.take_opioid(day=self.day)
        elif self.person.use_state == PersonUseState.DEPENDENT:
            # Once dependent, but before developing OUD, the person takes opioids if a
            # random draw is below their dependent use probability.
            if self.rng.random() < self.person.dependent_use_prob:
                self.person.take_opioid(day=self.day)
        elif self.person.use_state == PersonUseState.OUD_MILD:
            # With mild OUD, the person takes opioids every day.
            self.person.take_opioid(day=self.day)
        elif self.person.use_state == PersonUseState.OUD_MODERATE:
            # With moderate OUD, the person takes opioids once or twice a day. The decision
            # to take a second dose is determined by their risk tolerance.
            self.person.take_opioid(day=self.day)
            if self.rng.random() < (self.person.risk_tolerance - 1):
                self.person.take_opioid(day=self.day)
        elif self.person.use_state == PersonUseState.OUD_SEVERE:
            # With severe OUD, the person takes opioids between one and three times a day.
            # The decision to take second and third doses is determined by their risk tolerance.
            # to take a second dose is determined by their risk tolerance.
            self.person.take_opioid(day=self.day)
            if self.rng.random() < (self.person.risk_tolerance - 1):
                self.person.take_opioid(day=self.day)
            if self.rng.random() < (self.person.risk_tolerance - 1):
                self.person.take_opioid(day=self.day)
        else:
            raise ValueError(f"Unexpected person use state {self.person.use_state}")

