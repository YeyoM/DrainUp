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

# Parsing step
echo "Running the Parser now..."
python InferNERLogAll.py -full

# Conda deactivation
conda deactivate
echo "Exiting now..."
