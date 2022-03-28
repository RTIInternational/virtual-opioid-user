from os import walk
from pathlib import Path

import pandas as pd
from numpy import record
from tqdm import tqdm
from vou.batch import BatchSimulation


def get_scenario_dirs():
    scenario_dirs = []
    for root, dirs, files in walk(Path("experiment/scenarios")):
        if not dirs:
            scenario_dirs.append(root)
    return scenario_dirs


def record_results(batch_sim: BatchSimulation, output_dir: str):
    # record outcomes for each person in batch
    dose_increases = []
    overdose_counts = []
    overdose_any = []
    fatal_overdose = []

    for s in batch_sim.simulations:
        dose_increases.append(s.person.dose - s.person.starting_dose)
        overdoses = len(s.person.overdoses)
        overdose_counts.append(overdoses)
        overdose_any.append(1 if overdoses > 0 else 0)
        fatal_overdose.append(1 if len(s.person.concentration) < s.days * 100 else 0)

    # save as df
    results = {
        "overall_dose_increase": dose_increases,
        "overdose_count": overdose_counts,
        "overdose_any": overdose_any,
        "fatal_overdose": fatal_overdose,
    }
    df = pd.DataFrame(results)
    df.to_csv(Path(output_dir).joinpath("results.csv"))


def main():
    scenario_dirs = get_scenario_dirs()

    for d in tqdm(scenario_dirs, desc="Simulating scenario batches"):
        # print(f"Simulating batch for {dir}")
        batch_sim = BatchSimulation(
            params=Path(d).joinpath("params.json"),
            dynamic_params=Path("experiment/param_df.csv"),
        )
        batch_sim.simulate()

        record_results(batch_sim, d)


if __name__ == "__main__":
    main()
