# Virtual Opioid User

**Virtual Opioid User (VOU)** simulates an individual's opioid use over time.

**[Explore the app here!](https://share.streamlit.io/rtiinternational/virtual-opioid-user/main)**

**VOU is:**
- **Continuous:** opioid use is governed by continuous processes rather than discrete states and transition probabilities. 
- **Individual:** VOU simulates one person's life span at a time rather than a population. The goal is to explore how an individual's characteristics and environment (controlled via model parameters) affect their opioid use. 
- **Focused:** VOU models individuals who are already steady opioid users. VOU does not model individuals' path from absitence to use, or vice versa. 

## Contents
- `discrete_version` contains an older version of the model. It models an individual's use via discrete states rather than continuous processes. This model informed some aspects of the main model's structure. It is included for reference but does not affect the main model's functionality. 
- `inputs` contains all data files used in the simulation.
- `notebooks` contains some Jupyter notebooks which were used during development of some nmodel features. They are included for reference but do not affect the main model's functionality.
- `vou` contains the main Virtual Opioid User model, structured as a Python package. 

## Instructions

General users of the Virtual Opioid User app should use the app [on Streamlit Sharing](https://share.streamlit.io/rtiinternational/virtual-opioid-user/main) rather than through this repo. 

For app developers, here are some instructions to get started.

### Dependency management

This repo includes both `uv.lock` and `requirements.txt`. This is an unusual choice, motivated by the deployment on Streamlit Sharing (at the time of this decision, Streamlit did not have functionality to use `uv` for dependency management). 

This provides two options for running the app locally:

1. Create a virtual environment using `uv venv` and install the dependencies with `uv sync`.
1. Create a Python virtual environment using your tool of choice and install the dependencies with `pip install -r requirements.txt`. 

The big downside is keeping these files in sync. If you add dependencies using `uv add`, make sure to then run `uv export --format requirements-txt > requirements.txt`.

### Running the app locally

Run `streamlit run streamlit_app.py`. 
