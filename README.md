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

## Running the model
App users can [run the app on Streamlit Sharing](https://share.streamlit.io/rtiinternational/virtual-opioid-user/main). 

Developers wishing to run the app locally can follow these steps:

1. Clone this repository to your local machine.
1. Create a Python virtual environment. VOU was developed in Python 3.8. Other versions may cause compatibility issues.
1. Activate the virtual environment.
1. Install dependencies with `pip install -r requirements.txt`.
1. Run the Streamlit app with `streamlit run streamlit_app.py`

## Dependency management
This project uses `pip-tools` for dependency management. To add a dependency, follow these steps:

1. Install pip tools in your virtual environment: `pip install pip-tools`
1. Add the dependency to `requirements.in`
    - For experiment-specific dependencies, add the dependency to `experiment/requirements.in`
1. Run `pip-compile` to generate an updated `requirements.txt` based on the updated `requirements.in`

Do not add requirements directly to `requirements.txt`. They will be overwritten the next time someone runs `pip-compile`.
