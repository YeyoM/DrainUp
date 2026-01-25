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

# Trainer step
echo "Running the Trainer now..."
python TrainNERLogAll.py -full

# Conda deactivation
conda deactivate
echo "Exiting now..."
