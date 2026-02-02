#!/bin/bash

# GO TO EVAL DIR
echo "CDing into directory"
cd ../../../benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# Run the Verifier step
echo "Running The Verifier/Tester now..."
python verifier.py 

deactivate
echo "Exiting now..."
