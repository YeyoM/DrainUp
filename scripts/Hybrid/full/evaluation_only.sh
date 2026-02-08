#!/bin/bash

# GO TO EVAL DIR
echo "CDing into directory"
cd ../../../benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE EVALUATION STEP
echo "Running The Evaluation now..."
python evaluator.py -full -hybrid

deactivate
echo "Exiting now..."
