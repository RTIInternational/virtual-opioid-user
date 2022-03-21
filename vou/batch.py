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
    def __init__(self, params: Path, distribution_params: Path):
        self.params = load_json(params)
        self.dist_params = pd.read_csv(distribution_params)

    def simulate(self, parallel: bool = True):
        """
        Runs the specified number of simulations using the specified parameters.
        Generates the seeds for each simulation using the specified random number
        generator, allowing for reproducibility.
        """

        def simulate_one_person(self, param_dict: dict):
            person = Person(
                rng=Random(param_dict['seed']),
                starting_dose=param_dict["starting_dose"], #Could potentially sample from distributions here... or within the prepare.py file
                dose_increase=param_dict["dose_increase"],
                external_risk=param_dict["external_risk"],
                internal_risk=param_dict["internal_risk"],
                behavioral_variability=param_dict["behavioral_variability"],
            )
            simulation = Simulation(
                person=person,
                rng=Random(param_dict["seed"]),
                dose_variability=self.params["dose_variability"], 
                availability=param_dict["availability"],
                fentanyl_prob=self.params["fentanyl_prob"],
                counterfeit_prob=self.params["counterfeit_prob"],
            )
            simulation.simulate()
            return simulation

        if parallel is False:
            self.simulations = [simulate_one_person(self, dict(row)) for id, row in self.dist_params.iterrows()]

        if parallel is True:
            num_cores = multiprocessing.cpu_count()
            self.simulations = Parallel(n_jobs=num_cores)(
                delayed(simulate_one_person)(self, dict(row)) for id, row in self.dist_params.iterrows()
            )


if __name__ == "__main__":
    batch_sim = BatchSimulation(
        params=Path(
            "experiment/scenarios/counterfeit_prob_0.26/dose_var_0.3_fent_prob_0.25/high/params.json"
        ),
        distribution_params=Path("experiment/param_df.csv"),
    )

    batch_sim.simulate()

