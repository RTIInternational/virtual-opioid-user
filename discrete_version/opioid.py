class Opioid:
    def __init__(self, rng):
        self.rng = rng
        self.is_available = True

        # Set the doses available in terms of morphine milligram equivalents
        self.doses = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        # Set the probability of overdose for each dose.
        # This model was derived by fitting a zero-intercept linear model to the data
        # from Dasgupta et al. 2016.
        self.overdose_probability = [2.78041481e-07 * dose for dose in self.doses]

        # Set the lambda value for the exponential distribution governing
        # the probability of increasing to the next dose at each dose.
        #
        # Lambda = 1 / mean time to next dose
        #
        # As dose increases, the mean time to go to the next dose decreases.
        self.dose_increase_lambda = {
            10: 1 / 179,
            20: 1 / 143,
            30: 1 / 114,
            40: 1 / 92,
            50: 1 / 73,
            60: 1 / 59,
            70: 1 / 47,
            80: 1 / 38,
            90: 1 / 30,
        }

    def update_availability(self, prob_available: float = 0.9):
        """
        Updates self.is_available based on a random draw and specified probability
        of availability. 
        """
        if prob_available < 0 or prob_available > 1:
            raise ValueError(
                f"Probability of availability {prob_available} outside bounds of 0 and 1."
            )
        if self.rng.random() < prob_available:
            self.is_available = True
        else:
            self.is_available = False
