import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from vou.person import DoseIncreaseSource, Opioid, Person


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
    opioid: Opioid = Opioid.HYDROCODONE,
):
    """
    Generates a plot of the person's opioid concentration, habit, effect,
    desperation, and overdoses over time. Should be used after the person's
    opioid use has been simulated via Simulation.simulate(). Returns a
    matplotlib figure.

    Start day and duration parameters allow control over time frame shown.
    """
    dose_multiplier = person.params["mme_equivalents"][str(opioid)]

    palette = make_ibm_color_palette()
    start_time = 0 if start_day == 0 else start_day * 100
    duration_time = duration * 100
    end_time = start_time + duration_time

    fig, ax1 = plt.subplots(figsize=(16, 8))

    ax1.plot(
        range(start_time, end_time),
        [c / dose_multiplier for c in person.concentration[start_time:end_time]]
        + [0] * max(0, (end_time - start_time) - len(person.concentration)),
        label="Concentration",
        color=palette[0],
        zorder=0,
    )
    if show_habit:
        ax1.plot(
            range(start_time, end_time),
            [h / dose_multiplier for h in person.habit[start_time:end_time]]
            + [0] * max(0, (end_time - start_time) - len(person.habit)),
            label="Tolerance",
            color=palette[1],
            zorder=2,
        )
    if show_effect:
        ax1.plot(
            range(start_time, end_time),
            [e / dose_multiplier for e in person.effect[start_time:end_time]]
            + [0] * max(0, (end_time - start_time) - len(person.effect)),
            label="Effect",
            color=palette[2],
            zorder=1,
        )
    if len(person.concentration) < end_time:
        ax1.set_xlim(right=end_time)

    ax1.set_ylabel(f"Milligrams of {str(opioid)}")

    if show_desperation:
        ax2 = ax1.twinx()
        ax2.plot(
            range(start_time, end_time),
            [d / dose_multiplier for d in person.desperation[start_time:end_time]]
            + [0] * max(0, (end_time - start_time) - len(person.desperation)),
            label="Desperation",
            color=palette[3],
            zorder=3,
        )
        ax2.tick_params(axis="y")
        ax2.set_ylabel("Desperation (Arbitrary Units)")

        ax2.vlines(
            x=[od for od in person.overdoses if start_time <= od < end_time],
            ymin=0,
            ymax=max(person.concentration) / dose_multiplier,
            colors="black",
            linestyles="dotted",
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
            ymax=max(person.concentration) / dose_multiplier,
            colors="black",
            linestyles="dotted",
            label="OD",
            zorder=4,
        )
        ax1.legend()

    # transform dose increase record to plot sources over time
    color_map = {
        DoseIncreaseSource.PRIMARY_DOCTOR: "limegreen",
        DoseIncreaseSource.SECONDARY_DOCTOR: "goldenrod",
        DoseIncreaseSource.DEALER: "firebrick",
    }

    dose_increases = {
        k: v for k, v in person.dose_increase_record.items() if v["success"] == True
    }
    dose_increase_times = [k for k in dose_increases.keys()]
    dose_increase_times.insert(0, 0)
    dose_increase_sources = [v["source"] for v in dose_increases.values()]
    dose_increase_sources.insert(0, DoseIncreaseSource.PRIMARY_DOCTOR)

    for i, t in enumerate(dose_increase_times):
        if i == len(dose_increase_times) - 1:
            xmax = end_time
        else:
            xmax = dose_increase_times[i + 1]
        ax1.hlines(
            y=-20,
            xmin=t,
            xmax=xmax,
            colors=color_map[dose_increase_sources[i]],
            label=str(dose_increase_sources[i]),
            lw=5,
        )

    def legend_without_duplicate_labels(ax):
        handles, labels = ax.get_legend_handles_labels()
        unique = [
            (h, l)
            for i, (h, l) in enumerate(zip(handles, labels))
            if l not in labels[:i]
        ]
        ax.legend(*zip(*unique))

    legend_without_duplicate_labels(ax1)

    ax1.set_xlabel("Day")
    scale = 100
    ticks_x = ticker.FuncFormatter(lambda x, pos: "{0:g}".format(x / scale))
    ax1.xaxis.set_major_formatter(ticks_x)

    return fig
