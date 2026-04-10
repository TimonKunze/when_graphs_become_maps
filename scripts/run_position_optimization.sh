#!/bin/bash

#!/bin/bash

# Define the scripts and their commands
scripts=(
    # "../src/run_congr_position_opt.py 110 --min-nb-pairs 15 --max-nb-pos 20 --save"
    # "../src/run_corre_position_opt.py 110 --save"
    # "../src/run_congr_position_opt.py 110 --min-nb-pairs 20 --max-nb-pos 20 --save"
    
    # "../src/run_congr_position_opt.py 110 102484B0 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 64 --max-len-paths 4 --save"
    # "../src/run_congr_position_opt.py 110 102484B0 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 64 --save"
    # "../src/run_corre_position_opt.py 110 102484B0 --save"
    
    # # Run on Bakery02:
     # "../src/run_congr_position_opt.py 110 10248905 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 72 --save"
     "../src/run_congr_position_opt.py 110 10248905 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 40 --max-len-paths 4 --corr-tol 10 --save"
     "../src/run_congr_position_opt.py 110 10248905 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 40 --max-len-paths 4 --corr-tol 20 --save"
     "../src/run_congr_position_opt.py 110 10248905 --min-nb-pairs 20 --max-nb-pos 20 --max-workers 40 --max-len-paths 4 --corr-tol 30 --save"
    #  "../src/run_corre_position_opt.py 110 10248905 --save"
)

# Loop through the scripts
for i in "${!scripts[@]}"; do
    echo "Running script: ${scripts[$i]}..."
    # time python3 ${scripts[$i]}
    python3 ${scripts[$i]}
    
    # Check if the script executed successfully
    if [ $? -ne 0 ]; then
        echo "${scripts[$i]} failed."
        exit 1
    fi
done

echo "All scripts ran successfully."

