#!/bin/bash

#!/bin/bash

# Define the scripts and their commands
scripts=(
    "../src/run_vary_position_search.py 100 --save --atol 100 --max-workers 60 --chunk-size 300"  # former was grid110
    "../src/run_vary_position_search.py 90 --save --atol 90 --max-workers 30 --chunk-size 300"  # former was grid110
    "../src/run_vary_position_search.py 80 --save --atol 10 --max-workers 30 --chunk-size 300"  # former was grid110
    "../src/run_vary_position_search.py 40 --save --atol 10 --max-workers 30 --chunk-size 300"  # former was grid110
)

# Loop through the scripts
for i in "${!scripts[@]}"; do
    echo "Running script: ${scripts[$i]}..."
    time python3 ${scripts[$i]}
    # python3 ${scripts[$i]}
    
    # Check if the script executed successfully
    if [ $? -ne 0 ]; then
        echo "${scripts[$i]} failed."
        exit 1
    fi
done

echo "All scripts ran successfully."

