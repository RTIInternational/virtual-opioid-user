from vou.person import Person
from vou.simulation import Simulation

import json
import multiprocessing
from random import Random
from pathlib import Path
from joblib import Parallel, delayed


def load_json(json_file: Path):
    """
    Loads a JSON file to a JSON object
    """
    with open(json_file) as f:
        return json.load(f)


class BatchSimulation:
    def __init__(
        self, params: Path, seed: int, n_iterations: int,
    ):
        self.params = load_json(params)
        self.n_iterations = n_iterations
        self.rng = Random(seed)

    def simulate(self, parallel: bool = True):
        """
        Runs the specified number of simulations using the specified parameters.
        Generates the seeds for each simulation using the specified random number
        generator, allowing for reproducibility.
        """
        seeds = [self.rng.randint(1, 2 ** 31 - 1) for _ in range(self.n_iterations)]

        def simulate_one_person(self, seed: int):
            person = Person(
                rng=self.rng,
                starting_dose=self.params["starting_dose"],
                dose_increase=self.params["dose_increase"],
                base_threshold=self.params["base_threshold"],
                tolerance_window=self.params["tolerance_window"],
                external_risk=self.params["external_risk"],
                internal_risk=self.params["internal_risk"],
                behavior_when_resuming_use=self.params["behavior_when_resuming_use"],
            )
            simulation = Simulation(
                person=person,
                rng=self.rng,
                days=self.params["days"],
                stop_use_day=self.params["stop_use_day"],
                resume_use_day=self.params["resume_use_day"],
                dose_variability=self.params["dose_variability"],
                availability=self.params["availability"],
                fentanyl_prob=self.params["fentanyl_prob"],
            )
            simulation.simulate()
            return person

        if parallel is False:
            self.people = [simulate_one_person(s) for s in seeds]

        if parallel is True:
            num_cores = multiprocessing.cpu_count()
            self.people = Parallel(n_jobs=num_cores)(
                delayed(simulate_one_person)(s) for s in seeds
            )
