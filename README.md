# Virtual Opioid User

**Virtual Opioid User (VOU)** simulates an individual's opioid use over time. 

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
VOU is built as a Streamlit app. Once released, it will be hosted on Streamlit Sharing for public access. During development, you can run the app locally. To do so, follow these steps:

1. Clone this repository to your local machine.
1. Create a Python virtual environment. VOU was developed in Python 3.8. Other versions may cause compatibility issues.
1. Activate the virtual environment.
1. Install dependencies with `pip install -r requirements.txt`.
1. Run the Streamlit app with `streamlit run streamlit_app.py`
