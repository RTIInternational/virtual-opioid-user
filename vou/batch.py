import json
import multiprocessing
from pathlib import Path
from random import Random

from joblib import Parallel, delayed

from vou.person import Person
from vou.simulation import Simulation


def load_json(json_file: Path):
    """
    Loads a JSON file to a JSON object
    """
    with open(json_file) as f:
        return json.load(f)


class BatchSimulation:
    def __init__(self, params: Path, seeds: Path):
        self.params = load_json(params)
        with open(seeds) as f:
            self.seeds = f.read().splitlines()

    def simulate(self, parallel: bool = True):
        """
        Runs the specified number of simulations using the specified parameters.
        Generates the seeds for each simulation using the specified random number
        generator, allowing for reproducibility.
        """

        def simulate_one_person(self, seed: int):
            person = Person(
                rng=Random(seed),
                starting_dose=self.params["starting_dose"],
                dose_increase=self.params["dose_increase"],
                external_risk=self.params["external_risk"],
                internal_risk=self.params["internal_risk"],
                behavioral_variability=self.params["behavioral_variability"],
            )
            simulation = Simulation(
                person=person,
                rng=Random(seed),
                dose_variability=self.params["dose_variability"],
                availability=self.params["availability"],
                fentanyl_prob=self.params["fentanyl_prob"],
                counterfeit_prob=self.params["counterfeit_prob"],
            )
            simulation.simulate()
            return simulation

        if parallel is False:
            self.simulations = [simulate_one_person(self, s) for s in self.seeds]

        if parallel is True:
            num_cores = multiprocessing.cpu_count()
            self.simulations = Parallel(n_jobs=num_cores)(
                delayed(simulate_one_person)(self, s) for s in self.seeds
            )


if __name__ == "__main__":
    batch_sim = BatchSimulation(
        params=Path(
            "experiment/scenarios/counterfeit_prob_0.26/dose_var_0.3_fent_prob_0.25/high/params.json"
        ),
        seeds=Path("./scenarios/seeds.txt"),
    )

    batch_sim.simulate()

