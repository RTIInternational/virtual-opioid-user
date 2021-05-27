# Virtual Opioid User

*This directory contains files related to the **Virtual Opioid User (VOU)** model. This model is functionally separate from the main opioid policy model in the parent directory. Once released, it will be spun off from the `opioid-policy-model` repository into its own repository.* 

**Virtual Opioid User (VOU)** simulates an individual's opioid use over time. 

**VOU is:**
- **Continuous:** opioid use is governed by continuous processes rather than discrete states and transition probabilities. 
- **Individual:** VOU simulates one person's life span at a time rather than a population. The goal is to explore how an individual's characteristics and environment (controlled via model parameters) affect their opioid use. 
- **Focused:** VOU models individuals who are already steady opioid users. VOU does not model individuals' path from absitence to use, or vice versa. 

## Running the model

VOU is built as a Streamlit app. Once released, it will be hosted on Streamlit Sharing for public access. During development, you can run the app locally. Follow these steps:
1. Clone this repository to your local machine.
1. From the repository root, `cd vou`.
1. Create a Python virtual environment. VOU was developed in Python 3.8. Other versions may cause compatibility issues.
1. Activate the virtual environment.
1. Install dependencies with `pip install -r requirements.txt`.
1. Run the Streamlit app with `streamlit run vou/streamlit_app.py`
