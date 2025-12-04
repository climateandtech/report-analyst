#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install or upgrade dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run report_analyst/streamlit_app.py 