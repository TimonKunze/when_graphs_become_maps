# Code and data repository for the behavioral Experiment "When Graphs become Maps" 

Code and materials for a behavioral experiment on graph learning, graph layout, and spatial congruency.

## Repository layout

- `src/`: Python package for data cleaning, augmentation, graph utilities, statistics, and plotting.
- `data/raw_data/`: raw `.jsonl` exports from the web experiment.
- `data/tidy_data/`: cleaned CSV files created from the raw data.
- `data/graphs/`: generated graphs, graph positions, and random-position resources.
- `notebooks/`: analysis notebooks.
- `scripts/`: helper scripts
- `task_web_app/`: browser-based experiment

## Setup

This project expects Python 3.9.x and a standard scientific Python stack.

```bash
conda create -n graph-space python=3.9.13
conda activate graph-space
pip install -e .
```

Some analysis scripts also rely on packages such as `pandas`, `numpy`, `scipy`, `scikit-learn`, `networkx`, `seaborn`, `opencv-python`, and `scikit-image`. Install any missing packages in the active environment as needed.

## Typical workflow

1. Put raw experiment files into `data/raw_data/<condition>/<batch>/`.
2. Clean raw JSONL data into task-level CSVs with `src/data_cleaning.py`, creating files in  `data/tidy_data/<condition>/<batch>/`. or insert tidied data directly.
3. Use the notebooks in `notebooks/` or the plotting/statistics helpers in `src/` for analysis.

Useful entry points:
- `python /work/src/data_cleaning.py`
- `python /work/src/augment_data.py`
- `python /work/src/graph_lex.py`

The path configuration is centralized in [config.py](/work/src/config.py). Most scripts assume the repository root structure remains unchanged.

## Web experiment

The experiment frontend lives in `task_web_app/`. Open `task_web_app/index.html` through a web server for local testing. The data-saving endpoint and deployment notes are documented in [README.md](/work/task_web_app/exp_data/README.md).

## Data Download

The behavioral online data can be downloaded from [10.5281/zenodo.19472209](https://doi.org/10.5281/zenodo.19472209). The original participant IDs have been anonymized.
