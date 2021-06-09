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
    col1, col2 = st.beta_columns([1, 3])

    with col1:
        user_chars = st.beta_expander("User Characteristics")
        with user_chars:
            external_risk = st.number_input(
                label="Enter the user's environmental risk level between 0 and 1\n(composite of EXTERNAL factors motivating the user to use/increase dose)",
                min_value=0.05,
                max_value=1.0,
                value=0.5,
                step=0.05,
            )
            internal_risk = st.number_input(
                label="Enter the user's biological risk level between 0 and 1\n(composite of INTERNAL factors motivating the user to use/increase dose)",
                min_value=0.05,
                max_value=1.0,
                value=0.5,
                step=0.05,
            )
        sim_params = st.beta_expander("Simulation Parameters")
        with sim_params:
            starting_dose = st.slider(
                label="Select the user's starting dose in MME",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
            )
            dose_increase = st.slider(
                label="Select the amount the user will add when increasing dose",
                min_value=10,
                max_value=100,
                value=25,
                step=5,
            )
            dose_variability = st.slider(
                label="Select the variability of daily dose relative to user's preferred dose",
                min_value=0.0,
                max_value=0.5,
                value=0.1,
                step=0.05,
            )
            availability = st.slider(
                label="Select probability that opioids will be available on a given day",
                min_value=0.1,
                max_value=1.0,
                value=0.75,
                step=0.05,
            )
            fentanyl_prob = st.slider(
                label="Select probability that a given dose will be contaminated with fentanyl",
                min_value=0.0,
                max_value=0.05,
                value=0.001,
                step=0.001,
            )
            use_mode = st.selectbox(
                label="Select user behavior pattern",
                options=[
                    "Keep using entire time",
                    "Stop using halfway through",
                    "Stop using then resume at same dose",
                    "Stop using then resume at lower dose",
                ],
                index=0,
            )
            seed = st.number_input(
                label="Set the seed for the simulation's random number generator\n(optional - allows replication of results)",
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
        detail_viz_options = st.beta_expander("Visualization Options")
        with detail_viz_options:
            show_detail_viz = st.checkbox(label="Show detail plot?", value=False)
            detail_viz_start = st.slider(
                label="Select starting day of detail plot",
                min_value=0,
                max_value=730,
                value=0,
                step=10,
            )
            detail_viz_duration = st.slider(
                label="Select duration in days of detail plot",
                min_value=10,
                max_value=200,
                value=30,
                step=5,
            )

    with col2:
        fig = visualize(sim)
        st.pyplot(fig, dpi=300)
        if show_detail_viz is True:
            detail_fig = visualize(
                sim, start_day=detail_viz_start, duration=detail_viz_duration
            )
            st.pyplot(detail_fig, dpi=300)
