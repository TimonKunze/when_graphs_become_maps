#!/bin/bash

# Define the scripts and their commands
scripts=(
    # # 1st round of runs
    # "../src/run_graph_search.py 6 7 --max-workers 8 --save"
    # "../src/run_graph_search.py 6 8 --max-workers 8 --save"
    # "../src/run_graph_search.py 6 9 --max-workers 8 --save"
    # "../src/run_graph_search.py 7 6 --max-workers 8 --save"
    # "../src/run_graph_search.py 7 7 --max-workers 8 --save"
    # "../src/run_graph_search.py 7 8 --max-workers 8 --save"
    # "../src/run_graph_search.py 7 9 --max-workers 8 --save"
    # "../src/run_graph_search.py 8 6 --max-workers 8 --save"
    # "../src/run_graph_search.py 8 7 --max-workers 8 --save"
    # "../src/run_graph_search.py 8 8 --max-workers 8 --save"
    # "../src/run_graph_search.py 8 9 --max-workers 8 --save"
    # # 2nd round of runs
    # "../src/run_graph_search.py 9 7 --max-workers 20 --save"
    # "../src/run_graph_search.py 9 8 --max-workers 20 --save"
    # "../src/run_graph_search.py 9 9 --max-workers 20 --save"

    "../src/run_graph_search.py 9 10 --max-workers 30 --save"
    "../src/run_graph_search.py 9 11 --max-workers 30 --save"
    "../src/run_graph_search.py 10 7 --max-workers 30 --save"
    "../src/run_graph_search.py 10 8 --max-workers 30 --save"
    "../src/run_graph_search.py 10 9 --max-workers 30 --save"
    "../src/run_graph_search.py 10 10 --max-workers 30 --save"
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
