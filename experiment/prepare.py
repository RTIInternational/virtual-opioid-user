import json
from copy import deepcopy
from pathlib import Path
from shutil import rmtree

import fire
import numpy as np
import pandas as pd


class Experiment:
    def __init__(
        self,
        n_iterations: int,
        rng: np.random.Generator,
        default_params: Path,
        experiment_params: Path,
        n_samples: int
        
    ):
        self.n_iterations = n_iterations
        self.rng = rng
        self.default_params = self.load_json(default_params)
        self.experiment_params = self.load_json(experiment_params)
        self.n_samples = n_samples

        # self.covariate_values = self.draw_covariate_values()

    def load_json(self, path: Path):
        with open(path) as f:
            return json.load(f)

    def make_scenario_df(self):

        starting_dose_dist = self.rng.triangular(
            left=self.experiment_params['covariate_distributions']['triangular']['starting_dose']['left'],
            right=self.experiment_params['covariate_distributions']['triangular']['starting_dose']['right'],
            mode=self.experiment_params['covariate_distributions']['triangular']['starting_dose']['mode'],
            size=self.n_samples
        ) 

        dose_increase_dist = self.rng.triangular(
            left=self.experiment_params['covariate_distributions']['triangular']['dose_increase']['left'],
            right=self.experiment_params['covariate_distributions']['triangular']['dose_increase']['right'],
            mode=self.experiment_params['covariate_distributions']['triangular']['dose_increase']['mode'],
            size=self.n_samples
        ) 

        behavioral_variability_dist = self.rng.triangular(
            left=self.experiment_params['covariate_distributions']['triangular']['behavioral_variability']['left'],
            right=self.experiment_params['covariate_distributions']['triangular']['behavioral_variability']['right'],
            mode=self.experiment_params['covariate_distributions']['triangular']['behavioral_variability']['mode'],
            size=self.n_samples
        ) 

        availability_dist = self.rng.triangular(
            left=self.experiment_params['covariate_distributions']['triangular']['availability']['left'],
            right=self.experiment_params['covariate_distributions']['triangular']['availability']['right'],
            mode=self.experiment_params['covariate_distributions']['triangular']['availability']['mode'],
            size=self.n_samples
        ) 

        risk_params = self.experiment_params["covariate_distributions"][
            "multivariate_normal"
        ]["risk"]

        risk_array = self.rng.multivariate_normal(
            mean=np.array(risk_params["mean"]),
            cov=np.array(risk_params["cov"]),
            size=self.n_samples
        )

        risk_array = np.where(risk_array < 0, 0, risk_array)
        risk_array = np.where(risk_array > 1, 1, risk_array)

        covariate_df = pd.DataFrame(
            {
                'starting_dose':starting_dose_dist,
                'dose_increase':dose_increase_dist,
                'behavioral_variability':behavioral_variability_dist,
                'availability':availability_dist,
                'internal_risk':risk_array[:, 1],
                "external_risk":risk_array[:, 0],
            }
        )

        covariate_df['seed'] = [self.rng.integers(1, 2 ** 31 - 1) for _ in range(self.n_samples)]

        covariate_df.to_csv(Path("experiment/param_df.csv"), index=False)

        #return covariate_df

    def make_scenario_dirs(self):
        """
        Make dir for each scenario following

        - counterfeit_prob_x
            - dose_variability_x OR fentanyl_prob_X

        Each folder gets its own scenario default params. Then transform params only updates covariates.

        A final function should loop thru N iterations and transform params in each scenario N times.
        """

        for cprob in self.experiment_params["IV_levels"]["counterfeit_prob"]:
            for dvar in self.experiment_params["IV_levels"]["dose_variability"]:
                for fprob in self.experiment_params["IV_levels"]["fentanyl_prob"]:

                    scenario_dir = Path(
                        f"experiment/scenarios/counterfeit_prob_{cprob}/dose_var_{dvar}_fent_prob_{fprob}"
                    )
                    scenario_dir.mkdir(parents=True, exist_ok=True)

                    scenario_params = deepcopy(self.default_params)

                    scenario_params["counterfeit_prob"] = cprob
                    scenario_params["dose_variability"] = dvar
                    scenario_params["fentanyl_prob"] = fprob

                    with open(scenario_dir.joinpath("params.json"), "w") as f:
                        json.dump(scenario_params, f)

                    #print(scenario_params)

    def draw_covariate_values(self):
        covariate_values = {}

        for cov_name, cov_params in self.experiment_params["covariate_distributions"][
            "triangular"
        ].items():
            covariate_values[cov_name] = self.rng.triangular(
                left=cov_params["left"],
                mode=cov_params["mode"],
                right=cov_params["right"],
                size=self.n_iterations,
            )

        risk_params = self.experiment_params["covariate_distributions"][
            "multivariate_normal"
        ]["risk"]
        risk_array = self.rng.multivariate_normal(
            mean=np.array(risk_params["mean"]),
            cov=np.array(risk_params["cov"]),
            size=self.n_iterations,
        )
        risk_array = np.where(risk_array < 0, 0, risk_array)
        risk_array = np.where(risk_array > 1, 1, risk_array)

        covariate_values["external_risk"] = risk_array[:, 0]
        covariate_values["internal_risk"] = risk_array[:, 1]

        covariate_df = pd.DataFrame(covariate_values)
        return covariate_df

    def draw_seeds(self):
        seeds = [self.rng.integers(1, 2 ** 31 - 1) for _ in range(self.n_iterations)]
        seeds_file = Path("experiment/scenarios/seeds.txt")
        with open(seeds_file, mode="w") as f:
            for seed in seeds:
                f.write(str(seed))
                f.write("\n")

    def prepare(self):
        self.make_scenario_df()
        self.make_scenario_dirs()
        #self.draw_seeds()


def main(seed: int = 1, n_iterations: int = 100, n_samples: int=10):
    rng = np.random.default_rng(seed)
    if Path("experiment/scenarios").exists():
        rmtree(Path("experiment/scenarios"))
    experiment = Experiment(
        n_iterations=n_iterations,
        rng=rng,
        default_params=Path("experiment/default_params.json"),
        experiment_params=Path("experiment/experiment_params.json"),
        n_samples=n_samples,
    )
    experiment.prepare()


if __name__ == "__main__":
    fire.Fire(main)
