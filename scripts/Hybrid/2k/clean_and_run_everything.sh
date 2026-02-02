#!/usr/bin/zsh

# 0. Pre Script ==============================================================
source ~/.zshrc

# logging setup (simple)
LOGDIR=~/tesina/DrainUP/logs
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/run_$(date '+%Y%m%d_%H%M%S').log"
echo "Logging to: $LOGFILE"
exec > >(tee -a "$LOGFILE") 2>&1

# Make python unbuffered so output appears in real time
export PYTHONUNBUFFERED=1

# Cleanup
echo "Deleting Previous Results (~/tesina/DrainUP/result/)"
ls -la ~/tesina/DrainUP/result
rm -rf ~/tesina/DrainUP/result

echo "Cleanup completed, starting the parsing..."

# 1. Drain ===================================================================
echo "CDing into directory"
cd ~/tesina/DrainUP/benchmark/logparser/Drain
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE PARSING ONLY (CUSTOM SCRIPT)
echo "Running Drain now..."
python run_drain.py -otc

deactivate

# 2. UniParser ===============================================================
echo "CDing into UniParser directory"
cd ~/tesina/DrainUP/benchmark/logparser/UniParser
pwd

# Conda activation
export CUDA_VISIBLE_DEVICES=1
conda activate UniParser
unset LD_LIBRARY_PATH
which python

# Pre-processing step
echo "Skipping pre-processing step"
# echo "Running the Pre-processing step now..."
# python process_log_parsing_input_to_ner.py

# Trainer step
echo "Skipping training step"
# echo "Running the Trainer now..."
# python TrainNERLogAll.py

# Parsing step
echo "Running UniParser (parsing step) now..."
python InferNERLogAll.py

# Conda deactivation
conda deactivate
echo "UniParser Completed running"

# 3. Merge ===================================================================
echo "CDing into Merge directory"
cd ~/tesina/DrainUP/benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE MERGE STEP
echo "Running The Merge Results scripts now..."
python merge_results.py -otc 

deactivate

# 4. Eval ====================================================================
echo "CDing into Evaluation directory"
cd ~/tesina/DrainUP/benchmark/evaluation
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# RUN THE EVALUATION STEP
echo "Running The Evaluation now..."
python evaluator.py -otc -hybrid

deactivate
echo "Finished. Exiting now..."

