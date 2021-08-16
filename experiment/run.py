from vou.batch import BatchSimulation
from fire import Fire
from scipy.stats import skew, kurtosis
import numpy as np

from os import walk
from pathlib import Path
from csv import DictWriter


def get_scenario_dirs():
    scenario_dirs = []
    for root, dirs, files in walk(Path("experiment/scenarios")):
        if not dirs:
            scenario_dirs.append(root)
    return scenario_dirs


def summarize(batch_sim: BatchSimulation, output_dir: str):
    # record outcomes for each person in batch
    dose_increases = []
    overdose_counts = []
    for p in batch_sim.people:
        dose_increases.append(p.preferred_dose[-1] - p.preferred_dose[0])
        overdose_counts.append(len(p.overdoses))
    # summarize outcomes across people
    summary = {}
    summary["parameter"] = output_dir.split("/")[-2]
    summary["value"] = output_dir.split("/")[-1]
    summary["n_iterations"] = len(batch_sim.people)
    for name, outcome in {
        "dose_increase": dose_increases,
        "overdose_count": overdose_counts,
    }.items():
        summary[f"{name}_mean"] = np.mean(outcome)
        summary[f"{name}_median"] = np.median(outcome)
        summary[f"{name}_sd"] = np.std(outcome)
        summary[f"{name}_skewness"] = skew(outcome)
        summary[f"{name}_kurtosis"] = kurtosis(outcome)
    # write to csv
    with open(Path(output_dir).joinpath("summary.csv"), "w") as f:
        writer = DictWriter(f, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)


def run(seed: int = 1, n_iterations: int = 10):
    scenario_dirs = get_scenario_dirs()

    for dir in scenario_dirs:
        print(f"Simulating batch for {dir}")
        batch_sim = BatchSimulation(
            params=Path(dir).joinpath("params.json"),
            seed=seed,
            n_iterations=n_iterations,
        )
        batch_sim.simulate()

        summarize(batch_sim, dir)


if __name__ == "__main__":
    Fire(run)
