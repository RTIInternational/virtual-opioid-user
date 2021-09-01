from vou.person import Person, BehaviorWhenResumingUse
from vou.simulation import Simulation
from vou.visualize import visualize

from random import Random

import streamlit as st


@st.cache
def simulate(
    rng: Random,
    starting_dose: int = 50,
    dose_increase: int = 25,
    base_threshold: float = 0.0001,
    tolerance_window: int = 3_000,
    external_risk: float = 0.5,
    internal_risk: float = 0.5,
    behavior_when_resuming_use: BehaviorWhenResumingUse = None,
    days: int = 730,
    stop_use_day: int = None,
    resume_use_day: int = None,
    dose_variability: float = 0.1,
    availability: float = 0.9,
    fentanyl_prob: float = 0.0001,
):
    """
    Streamlit cached function to instantiate a Person and Simulation and run the
    simulation. Looks a bit repetitive, but this allows us to take advantage of
    Streamlit caching and avoid running the simulation repeatedly when an app user
    changes visualization parameters.
    """
    person = Person(
        rng=rng,
        starting_dose=starting_dose,
        dose_increase=dose_increase,
        base_threshold=base_threshold,
        tolerance_window=tolerance_window,
        external_risk=external_risk,
        internal_risk=internal_risk,
        behavior_when_resuming_use=behavior_when_resuming_use,
    )
    simulation = Simulation(
        person=person,
        rng=rng,
        days=days,
        stop_use_day=stop_use_day,
        resume_use_day=resume_use_day,
        dose_variability=dose_variability,
        availability=availability,
        fentanyl_prob=fentanyl_prob,
    )
    simulation.simulate()
    return person


if __name__ == "__main__":

    st.set_page_config(layout="wide")
    st.title("Virtual Opioid User")
    col1, col2 = st.columns([1, 3])

    with col1:
        readme = st.expander("README")
        with readme:
            st.markdown(
                """
                Virtual Opioid User (VOU) simulates an individual's opioid use over time.

                #### Reading the plot
                - *Concentration* represents the amount of opioid, in morphine milligram equivalents,
                in the user's system at a given time.

                - *Effect* represents the user's perception of the opioid's effect. When their habit
                increases, a given dose will have less effect.

                - *Habit* represents the user's adaptation to past doses. When they take a dose many
                times in succession, their habit increases, reducing their perceived effect.

                - *Discomfort* represents the user's withdrawal symptoms and craving for opioids.
                Increased discomfort motivates the user to take another dose.

                #### Using the app
                By adjusting user characteristics and model parameters, you can explore how
                various internal and external factors affect the user's opioid use trajectory.
                
                For example, try increasing the user's starting dose. Users with a high starting
                dose are more likely to increase their dose over time.

                Hover on the (?) icon next to each parameter for additional info.

                Note: VOU does not model any irregular/recreational opioid use prior to the
                start of daily opioid use.
                """
            )
        user_chars = st.expander("User Characteristics")
        with user_chars:
            external_risk = st.number_input(
                label="Enter the user's social risk level",
                help="Social risk represents a composite of external/environmental factors (e.g. social determinants of health) motivating the user to use opioids and seek increased effects from them. For example, individuals with less economic opportunity or more adverse childhood experiences are more likely to develop opioid use disorder.",
                min_value=0.05,
                max_value=1.0,
                value=0.5,
                step=0.05,
            )
            internal_risk = st.number_input(
                label="Enter the user's individual risk level",
                help="Individual risk represents a composite of psychological/biological factors (e.g. risk tolerance) motivating the user to use opioids and seek increased effects from them. For example, individuals with mental health disorders or other comorbidities are more likely to develop opioid use disorder.",
                min_value=0.05,
                max_value=1.0,
                value=0.5,
                step=0.05,
            )
        sim_params = st.expander("Simulation Parameters")
        with sim_params:
            starting_dose = st.slider(
                label="Select the user's starting dose in MME",
                help="The user starts the simulation taking their preferred dose consistently. This parameter controls their preferred dose at the start of the simulation.",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
            )
            dose_increase = st.slider(
                label="Select the amount the user will add when increasing dose",
                help="When the user is no longer satisfied with the effect of their preferred dose, they may increase their preferred dose. This parameter controls the amount by which they will increase their preferred dose.",
                min_value=10,
                max_value=50,
                value=25,
                step=5,
            )
            dose_variability = st.slider(
                label="Select the variability of dosage",
                help="Due to variability in supply and dose measurement, the user's doses may fluctuate from their preferred dose. This parameter controls the proportion by which doses will fluctuate relative to the user's preferred dose.",
                min_value=0.0,
                max_value=0.5,
                value=0.1,
                step=0.05,
            )
            availability = st.slider(
                label="Select probability that opioids will be available per day",
                help="For various reasons (e.g. supply, ability to pay), the user may not always be able to get opioids when they want to. The model updates opioid availability each day. This parameter controls the probability that opioids will be available each day.",
                min_value=0.1,
                max_value=1.0,
                value=0.75,
                step=0.05,
            )
            fentanyl_prob = st.slider(
                label="Select probability of fentanyl adulteration per dose",
                help="In addition to regular variability of dose, some opioid batches may be far more potent than expected due to adulteration with powerful synthetic opioids like fentanyl. This parameter controls the probability that a given dose will be adulterated with a synthetic opioid.",
                min_value=0.0,
                max_value=0.05,
                value=0.001,
                step=0.001,
            )
            use_mode = st.selectbox(
                label="Select user behavior pattern",
                help="To explore how outcomes change when the user changes their behavior, the simulation includes four fixed user behavior patterns.",
                options=[
                    "Keep using entire time",
                    "Stop using halfway through",
                    "Stop using then resume at same dose",
                    "Stop using then resume at lower dose",
                ],
                index=0,
            )
            seed = st.number_input(
                label="Set the simulation's random seed",
                help="Many of the model's processes are stochastic (i.e. randomly varying over time). This optional parameter allows replication of results. For a given set of parameters, the results will always be the same when the seed is kept constant. On the other hand, you can change the seed to explore different possible results for the same set of parameters.",
                min_value=1,
                max_value=100_000,
                value=1,
                step=1,
            )

    if use_mode == "Keep using entire time":
        stop_use_day = None
        resume_use_day = None
        behavior_when_resuming_use = None
        detail_viz_start = 1
    elif use_mode == "Stop using halfway through":
        stop_use_day = 360
        resume_use_day = None
        behavior_when_resuming_use = None
        detail_viz_start = 350
    elif use_mode == "Stop using then resume at same dose":
        stop_use_day = 360
        resume_use_day = 540
        behavior_when_resuming_use = BehaviorWhenResumingUse.SAME_DOSE
        detail_viz_start = 530
    elif use_mode == "Stop using then resume at lower dose":
        stop_use_day = 360
        resume_use_day = 540
        behavior_when_resuming_use = BehaviorWhenResumingUse.LOWER_DOSE
        detail_viz_start = 530

    sim = simulate(
        rng=Random(seed),
        starting_dose=starting_dose,
        dose_increase=dose_increase,
        external_risk=external_risk,
        internal_risk=internal_risk,
        behavior_when_resuming_use=behavior_when_resuming_use,
        stop_use_day=stop_use_day,
        resume_use_day=resume_use_day,
        dose_variability=dose_variability,
        availability=availability,
        fentanyl_prob=fentanyl_prob,
    )

    with col1:
        viz_options = st.expander("Visualization Options")
        with viz_options:
            show_desperation = st.checkbox(
                label="Show discomfort?",
                help="Discomfort represents the user's withdrawal symptoms and craving for opioids. Increased discomfort motivates the user to take another dose.",
                value=False,
            )
            show_effect = st.checkbox(
                label="Show effect?",
                help="Effect represents the user's perception of the opioid's effect. When their habit increases, a given dose will have less effect.",
                value=True,
            )
            show_habit = st.checkbox(
                label="Show habit?",
                help="Habit represents the user's adaptation to past doses. When they take a dose many times in succession, their habit increases, reducing their perceived effect.",
                value=True,
            )
            show_zoomed_viz = st.checkbox(
                label="Show zoomed plot?",
                help="The zoomed plot allows you to zoom in on a shorter time period and view more detail.",
                value=False,
            )
            zoomed_viz_start = st.slider(
                label="Select starting day of zoomed plot",
                help="Check the x-axis of the main plot to estimate the starting day of the area you want to zoom in on.",
                min_value=0,
                max_value=730,
                value=0,
                step=10,
            )
            zoomed_viz_duration = st.slider(
                label="Select duration in days of zoomed plot",
                help="Shorter duration will allow you to see more detail.",
                min_value=10,
                max_value=200,
                value=30,
                step=5,
            )

    with col2:
        fig = visualize(
            sim,
            show_desperation=show_desperation,
            show_habit=show_habit,
            show_effect=show_effect,
        )
        st.pyplot(fig, dpi=300)
        if show_zoomed_viz is True:
            zoomed_fig = visualize(
                sim,
                start_day=zoomed_viz_start,
                duration=zoomed_viz_duration,
                show_desperation=show_desperation,
                show_habit=show_habit,
                show_effect=show_effect,
            )
            st.pyplot(zoomed_fig, dpi=300)
        st.markdown(
            "Copyright 2021 [RTI International](https://www.rti.org/). Virtual Opioid User is an open source project. The code base is on [GitHub](https://github.com/RTIInternational/virtual-opioid-user)."
        )
