#!/bin/bash

# GO TO DRAIN DIR
echo "CDing into directory"
cd ../benchmark/logparser/Drain
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE PARSING ONLY (CUSTOM SCRIPT)
echo "Running Drain now..."
python run_drain.py -otc

deactivate
echo "Exiting now..."
