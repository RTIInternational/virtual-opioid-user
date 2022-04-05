import json
import multiprocessing
from pathlib import Path
from random import Random
import pandas as pd

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
    def __init__(self, params: Path, dynamic_params: Path):
        self.params = load_json(params)
        self.dynamic_params = pd.read_csv(dynamic_params)

    def simulate(self, parallel: bool = True):
        """
        Runs the specified number of simulations using the specified parameters.
        Generates the seeds for each simulation using the specified random number
        generator, allowing for reproducibility.
        """

        def simulate_one_person(self, params: dict):

            rng = Random(params["seed"])

            person = Person(
                rng=rng,
                starting_dose=params[
                    "starting_dose"
                ],  # Could potentially sample from distributions here... or within the prepare.py file
                dose_increase=params["dose_increase"],
                external_risk=params["external_risk"],
                internal_risk=params["internal_risk"],
                behavioral_variability=params["behavioral_variability"],
            )
            simulation = Simulation(
                person=person,
                rng=rng,
                dose_variability=self.params["dose_variability"],
                availability=params["availability"],
                fentanyl_prob=self.params["fentanyl_prob"],
                counterfeit_prob=self.params["counterfeit_prob"],
            )
            simulation.simulate()
            return simulation

        if parallel is False:
            self.simulations = [
                simulate_one_person(self, dict(row))
                for id, row in self.dynamic_params.iterrows()
            ]

        if parallel is True:
            num_cores = multiprocessing.cpu_count()
            self.simulations = Parallel(n_jobs=num_cores)(
                delayed(simulate_one_person)(self, dict(row))
                for id, row in self.dynamic_params.iterrows()
            )


if __name__ == "__main__":
    batch_sim = BatchSimulation(
        params=Path(
            "experiment/scenarios/counterfeit_prob_0.26/dose_var_0.3_fent_prob_0.25/high/params.json"
        ),
        distribution_params=Path("experiment/param_df.csv"),
    )

    batch_sim.simulate()

