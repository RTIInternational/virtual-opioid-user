import matplotlib.pyplot as plt
import pandas as pd
from seaborn.palettes import color_palette

from vou.person import Person


def visualize_opioid_use(person: Person, seed: int):
    """
    Generate a plot showing a person's opioid use over time.
    """
    # First, convert the dosage data to a dataframe and group doses so multiple
    # doses per day are summed.
    days = pd.Series(person.opioid_dose.keys())
    doses = pd.Series(person.opioid_dose.values())
    states = pd.Series(person.use_state_over_time.values())
    dosage_by_day = pd.DataFrame({"day": days, "dose": doses, "state": states})
    dosage_by_day = dosage_by_day.groupby("day").agg(
        dose=("dose", "sum"), state=("state", "first")
    )
    dosage_by_day.reset_index(inplace=True)

    # Build the framework of the plot
    fig, ax = plt.subplots(figsize=[10, 5])
    pal = color_palette("muted")
    color_iterator = 0
    plt.title("Person's Opioid Use Over Time")
    plt.xlabel("Day")
    plt.ylabel("Dose")

    # Loop through use states to color bars by use state
    for st in dosage_by_day.state.unique():
        state_data = dosage_by_day[dosage_by_day.state.eq(st)]
        plt.bar(
            x=state_data["day"],
            height=state_data["dose"],
            color=pal[color_iterator],
            label=st,
        )
        color_iterator += 1

    # Add vertical lines to indicate OD
    plt.vlines(
        x=person.overdosed,
        ymin=0,
        ymax=max(doses),
        colors="black",
        linestyles="dashed",
        label="OD",
    )

    # Add a text box to show person's risk variables
    textstr = "\n".join(
        (
            f"Seed = {seed}",
            f"Risk Multiplier = {round(person.risk_multiplier, 2)}",
            f"Risk Tolerance = {round(person.risk_tolerance, 2)}",
        )
    )
    ax.text(
        0.02,
        0.5,
        textstr,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(facecolor="none", edgecolor="lightgrey"),
    )

    # Add a legend
    plt.legend()
