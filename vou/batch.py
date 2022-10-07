import json
import multiprocessing
from copy import deepcopy
from pathlib import Path
from random import Random

import pandas as pd
from joblib import Parallel, delayed

from vou.person import Person
from vou.simulation import Simulation
from vou.utils import load_json


class BatchSimulation:
    def __init__(self, params: Path, dynamic_params: Path, drug_parameter_path: Path):
        self.params = load_json(params)
        self.dynamic_params = pd.read_csv(dynamic_params)
        self.drug_parameter_path = drug_parameter_path

    def simulate(self, parallel: bool = True):
        """
        Runs the specified number of simulations using the specified parameters.
        Generates the seeds for each simulation using the specified random number
        generator, allowing for reproducibility.
        """

        def combined_static_and_dynamic_params(self, dynamic_param_row: dict):
            """
            Combines the static parameters which stay constant across simualtions in the batch
            with the dynamic parameters from one row of self.dynamic_params. This puts all the
            parameters for a single simulation into one dictionary.
            """
            # Make sure there aren't any params specified as both static and dynamic
            duplicate_params = [
                p for p in self.params.keys() if p in dynamic_param_row.keys()
            ]
            assert (
                len(duplicate_params) == 0
            ), f"The following params are included as both static and dynamic: {duplicate_params}"

            params = deepcopy(self.params)
            params.update(dynamic_param_row)

            # Make sure we have all the params we need
            needed_params = [
                "seed",
                "starting_dose",
                "dose_increase",
                "external_risk",
                "internal_risk",
                "behavioral_variability",
                "dose_variability",
                "availability",
                "fentanyl_prob",
                "counterfeit_prob",
            ]
            missing = [p for p in needed_params if p not in params.keys()]
            assert len(missing) == 0, f"The following params are missing: {missing}"

            return params

        def simulate_one_person(self, dynamic_param_row: dict):

            params = combined_static_and_dynamic_params(self, dynamic_param_row)

            rng = Random(params["seed"])

            person = Person(
                rng=rng,
                starting_dose=params["starting_dose"],
                dose_increase=params["dose_increase"],
                external_risk=params["external_risk"],
                internal_risk=params["internal_risk"],
                behavioral_variability=params["behavioral_variability"],
                drug_parameter_path=self.drug_parameter_path,
            )
            simulation = Simulation(
                person=person,
                rng=rng,
                dose_variability=params["dose_variability"],
                availability=params["availability"],
                fentanyl_prob=params["fentanyl_prob"],
                counterfeit_prob=params["counterfeit_prob"],
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
