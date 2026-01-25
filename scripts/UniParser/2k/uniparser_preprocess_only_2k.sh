#!/usr/bin/zsh
source ~/.zshrc

# GO TO UNIPARSER DIR
echo "CDing into directory"
cd ../../../benchmark/logparser/UniParser
pwd

# Conda activation
export CUDA_VISIBLE_DEVICES=1
conda activate UniParser
unset LD_LIBRARY_PATH
which python

# Pre-processing to NER format
echo "Running the Pre-processing step now..."
python process_log_parsing_input_to_ner.py

# Conda deactivation
conda deactivate
echo "Exiting now..."
