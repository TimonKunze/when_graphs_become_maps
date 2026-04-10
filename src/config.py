"""Config for the Graph vs. Space Project.

It defines a PATHS directionary for easy file path access
that is loaded from all other files.
"""
import seaborn as sns
from pathlib import Path

# Set Theme {{{

sns.set_theme(
    context='notebook',
    palette='Set2',
    style={'axes.spines.left': True,
           'axes.spines.bottom': True,
           'axes.spines.right': False,
           'axes.spines.top': False}
)
palette = sns.color_palette()
light_orange_palette = ["#edacae", "#fad4ba"]
dark_orange_palette = ["#dc575c", "#f4883a"]
light_brown_palette = ["#9e7a7a", "#ded2d2"]
dark_brown_palette = ["#5b4242", "#a78484"]
light_grey_palette = ["#CCCCCC", "#737373"]
dark_grey_palette = ["#4D4D4D", "#333333", ]
palette3 = sns.color_palette("muted")
palette4 = sns.color_palette("Set3")
palette5 = sns.color_palette("Set1")
dist_palette = sns.color_palette([
    "#65a2c8",
    "#ffd92f",
    "#c96a55",
    "#c96a55",
    "#c96a55",
    "#c38376",
    "#cb9387",
    "#bb6481",
    "#bb9f64",
    "#ff8284",
])

clust_palette = sns.color_palette([
    "#561a65",
    "#457799",
    "#49be86",
    "#fde93b",
    "#d2691e",
])
# }}}
# Paths {{{


def find_project_root():
    """Find root directory based on setup.py file."""
    # Start searching from the current file's directory or current
    # working directory
    current_dir = Path(__file__).resolve()
    # Traverse upwards in the directory structure
    for parent in current_dir.parents:
        if (
            parent / "setup.py"
        ).exists():  # Check if 'setup.py' exists in the directory
            return parent
    # If 'setup.py' is not found
    raise FileNotFoundError("Couldn't find 'setup.py' in any parent directory.")


PATHS = {}
PATHS["root"] = find_project_root()

# Data
PATHS["data"] = PATHS["root"] / "data"

# Results
PATHS["results"] = PATHS["root"] / "results"
PATHS["augmented_data"] = PATHS["results"] / "augmented_data"

# Analysis
PATHS["analysis"] = PATHS["root"] / "analysis"

# Docs
PATHS["docs"] = PATHS["root"] / "docs"

# Experiment Web app
PATHS["local_exp_data"] = PATHS["root"] / "task_web_app" / "exp_data"
PATHS["nodes"] = PATHS["root"] / "task_web_app" / "stimuli" / "flowers"

# Data
PATHS["raw_data"] = PATHS["data"] / "raw_data"
PATHS["tidy_data"] = PATHS["data"] / "tidy_data"

PATHS["sup-graphs"] = PATHS["data"] / "graphs"
PATHS["graphs"] = PATHS["sup-graphs"] / "generated_graphs"
PATHS["graphs_corr"] = PATHS["sup-graphs"] / "generated_graphs_corr"
PATHS["graph_pos"] = PATHS["sup-graphs"] / "generated_graph_positions"
PATHS["graph_pos_varied"] = PATHS["sup-graphs"] / "varied_graph_positions"
PATHS["graph_pos_unconstr"] = PATHS["sup-graphs"] / "varied_graph_pos_unconstr"
PATHS["random_graphs"] = PATHS["sup-graphs"] / "random_graphs"

group_folders = ["rotational", "unconstrained"]
for group in group_folders:
    PATHS["raw-" + group] = PATHS["raw_data"] / group
    PATHS["tidy-" + group] = PATHS["tidy_data"] / group
    for pilot_nb in range(1, 7 + 1):
        PATHS[f"pilot{pilot_nb}-raw-" + group] = (
            PATHS["raw_data"] / group / f"pilot_{pilot_nb}"
        )
        PATHS[f"pilot{pilot_nb}-tidy-" + group] = (
            PATHS["tidy_data"] / group / f"pilot_{pilot_nb}"
        )
    for batch_nb in range(1, 3):
        PATHS[f"batch{batch_nb}-raw-" + group] = (
            PATHS["raw_data"] / group / f"batch_{batch_nb}"
        )
        PATHS[f"batch{batch_nb}-tidy-" + group] = (
            PATHS["tidy_data"] / group / f"batch_{batch_nb}"
        )

for pilot_nb in range(1, 7 + 1):
    PATHS[f"pilot{pilot_nb}-analysis"] = (
        PATHS["analysis"] / "behavioral" / f"pilot_{pilot_nb}"
    )
for batch_nb in range(1, 3):
    PATHS[f"batch{batch_nb}-analysis"] = (
        PATHS["analysis"] / "behavioral" / f"pilot_{batch_nb}"
    )
    PATHS[f"batch{batch_nb}-payment"] = (
        PATHS["data"] / "participant_payment" / f"batch_{batch_nb}"
    )


# }}}


if __name__ == "__main__":
    print(find_project_root())
