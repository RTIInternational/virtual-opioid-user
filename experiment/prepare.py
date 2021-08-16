from numpy import linspace, round, rint

import json
from pathlib import Path
from copy import deepcopy
from shutil import rmtree


def prepare_sweep_ranges():
    sweep_ranges = {}
    sweep_ranges["starting_dose"] = rint(linspace(10, 200, 20))
    sweep_ranges["variability"] = round(linspace(0, 0.5, 20), 2)
    sweep_ranges["fentanyl_prob"] = round(linspace(0, 0.05, 20), 3)
    sweep_ranges["availability"] = round(linspace(0.1, 1.0, 20), 2)
    return sweep_ranges


def load_default_params():
    with open("experiment/default_params.json") as f:
        return json.load(f)


def transform_params(default_params: dict, sweep_ranges: dict, param: str):
    for i in sweep_ranges[param]:
        Path(f"experiment/scenarios/{param}/{i}").mkdir(parents=True, exist_ok=True)
        transformed_params = deepcopy(default_params)
        transformed_params[param] = i
        with open(f"experiment/scenarios/{param}/{i}/params.json", "w") as f:
            json.dump(transformed_params, f)


if __name__ == "__main__":
    if Path("experiment/scenarios").exists():
        rmtree(Path("experiment/scenarios"))
    default_params = load_default_params()
    sweep_ranges = prepare_sweep_ranges()
    for param in sweep_ranges:
        transform_params(default_params, sweep_ranges, param)
