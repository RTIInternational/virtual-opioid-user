import pandas as pd
from matplotlib import pyplot as plt

from glob import glob
from pathlib import Path
import os

from vou.batch import load_json
from experiment.run import get_scenario_dirs


def read_scenario_results(scenario_dir: Path):
    results = pd.read_csv(scenario_dir.joinpath('summary.csv'))
    params = load_json(scenario_dir.joinpath('params.json'))

    for param_name, param_value in params.items():
        results[param_name] = param_value

    return results


def read_all_results():
    scenario_dirs = get_scenario_dirs()
    dfs = []

    for d in scenario_dirs:
        dfs.append(read_scenario_results(d))

    return pd.concat(dfs)


if __name__ == "__main__":

    outdir = Path("experiment/output")

    if not outdir.exists:
        outdir.mkdir()


