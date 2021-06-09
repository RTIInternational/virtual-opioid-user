from vou.person import Person

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def make_ibm_color_palette():
    """
    Returns a colorblind-friendly color palette from the IBM design library.
    See https://davidmathlogic.com/colorblind/#%23648FFF-%23785EF0-%23DC267F-%23FE6100-%23FFB000
    """
    return ["#648FFF", "#DC267F", "#FE6100", "#FFB000"]


def visualize(
    person: Person,
    start_day: int = 0,
    duration: int = 730,
    show_desperation: bool = False,
    show_habit: bool = True,
    show_effect: bool = True,
):
    """
    Generates a plot of the person's opioid concentration, habit, effect,
    desperation, and overdoses over time. Should be used after the person's
    opioid use has been simulated via Simulation.simulate(). Returns a
    matplotlib figure.

    Start day and duration parameters allow control over time frame shown.
    """
    palette = make_ibm_color_palette()
    start_time = 0 if start_day == 0 else start_day * 100
    duration_time = duration * 100
    end_time = start_time + duration_time

    fig, ax1 = plt.subplots(figsize=(16, 8))

    ax1.plot(
        person.concentration[start_time:end_time],
        label="Concentration",
        color=palette[0],
        zorder=0,
    )
    if show_habit:
        ax1.plot(
            person.habit[start_time:end_time], label="Habit", color=palette[1], zorder=2
        )
    if show_effect:
        ax1.plot(
            person.effect[start_time:end_time],
            label="Effect",
            color=palette[2],
            zorder=1,
        )

    ax1.set_ylabel("Morphine Milligram Equivalents (MME)")

    if show_desperation:
        ax2 = ax1.twinx()
        ax2.plot(
            person.desperation[start_time:end_time],
            label="Desperation",
            color=palette[3],
            zorder=3,
        )
        ax2.tick_params(axis="y")
        ax2.set_ylabel("Desperation (Arbitrary Units)")

        ax2.vlines(
            x=[od for od in person.overdoses if start_time <= od < end_time],
            ymin=0,
            ymax=max(person.concentration),
            colors="black",
            linestyles="dashed",
            label="OD",
            zorder=4,
        )

        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        lines = lines_1 + lines_2
        labels = labels_1 + labels_2
        ax1.legend(lines, labels)

    else:
        ax1.vlines(
            x=[od for od in person.overdoses if start_time <= od < end_time],
            ymin=0,
            ymax=max(person.concentration),
            colors="black",
            linestyles="dashed",
            label="OD",
            zorder=4,
        )
        ax1.legend()

    ax1.set_xlabel("Day")
    scale = 100
    ticks_x = ticker.FuncFormatter(lambda x, pos: "{0:g}".format(x / scale))
    ax1.xaxis.set_major_formatter(ticks_x)

    return fig
