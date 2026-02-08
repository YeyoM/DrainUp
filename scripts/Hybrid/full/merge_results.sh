#!/bin/bash

# GO TO EVAL DIR
echo "CDing into directory"
cd ../../../benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE MERGE RESULTS SCRIPT
echo "Running The Merge Results scripts now..."
python merge_results.py -full

deactivate
echo "Exiting now..."
