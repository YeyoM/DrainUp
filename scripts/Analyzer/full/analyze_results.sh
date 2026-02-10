#!/bin/bash

# GO TO EVAL DIR
echo "CDing into directory"
cd ../../../benchmark/analyzer
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source venv/bin/activate
which python

# RUN THE ANALYZER
echo "Running The Analyzer Script now..."
python analyzer_full.py 

deactivate
echo "Exiting now..."
