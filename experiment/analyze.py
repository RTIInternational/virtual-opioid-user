import pandas as pd
from matplotlib import pyplot as plt

from glob import glob
from pathlib import Path
import os


def make_string_pretty(string: str):
    return string.replace("_", " ").replace("prob", "probability").title()


def plot_param_sweep(param: str, outcome: str):
    # read data
    summaries = []
    for file in glob(f"experiment/scenarios/{param}/*/summary.csv"):
        summaries.append(pd.read_csv(file))
    df = pd.concat(summaries)
    df.sort_values("value", inplace=True)

    # extract values for plot
    x = df["value"]
    mean = df[f"{outcome}_mean"]
    sd = df[f"{outcome}_sd"]
    outcome_pretty = make_string_pretty(outcome)
    param_pretty = make_string_pretty(param)

    # plot
    fig, ax = plt.subplots(figsize=[6, 4])
    ax.plot(x, mean, label="Mean")
    ax.errorbar(
        x,
        mean,
        sd,
        color="None",
        ecolor="grey",
        elinewidth=1,
        capsize=3,
        zorder=0,
        label="SD",
    )

    ax.set_xlabel(param_pretty)
    ax.set_ylabel(outcome_pretty)
    ax.set_title(f"{outcome_pretty} over {param_pretty} Sweep")
    ax.legend()

    plt.savefig(f"experiment/output/{param}_sweep_plot.png", dpi=300)


if __name__ == "__main__":

    if not os.path.exists("experiment/output"):
        Path("experiment/output").mkdir()

    plot_param_sweep("fentanyl_prob", "overdose_count")
    plot_param_sweep("availability", "dose_increase")
    plot_param_sweep("starting_dose", "dose_increase")
    plot_param_sweep("variability", "dose_increase")

