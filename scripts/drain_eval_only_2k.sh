#!/bin/bash

# GO TO EVAL DIR
echo "CDing into directory"
cd ../benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE EVAL ONLY (CUSTOM SCRIPT)
echo "Running The Evaluation for Drain now..."
python evaluator.py -otc -drain

deactivate
echo "Exiting now..."
