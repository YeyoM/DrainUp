#!/bin/bash
# GO TO DRAIN DIR
echo "CDing into directory"
cd ../../../benchmark/logparser/Drain
pwd

# ACTIVATE THE PYTHON ENV
echo "Activating python env"
source .venv/bin/activate
which python

# CREATE LOG FILE WITH TIMESTAMP
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="../../../result/drain_run_${TIMESTAMP}.log"

echo "Running Drain now..."
echo "Output will be saved to: $LOG_FILE"

# RUN THE PARSING WITH OUTPUT REDIRECT
# Both stdout and stderr go to log file AND display on screen
python -u run_drain.py -full 2>&1 | tee "$LOG_FILE"

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

deactivate
echo "Exiting now..."
echo "Exit code: $EXIT_CODE"
echo "Full log saved to: $LOG_FILE"

# Print summary
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Script completed successfully!"
else
    echo "✗ Script exited with error code: $EXIT_CODE"
fi
