"""Augment data with extra information consisting of.

- add calculations of relevant distance matrices
- exclude participants that have incomplete data or answered yes or maybe
  at the cheater question
"""
import ast
import numpy as np
import pandas as pd
import networkx as nx
import cv2

from collections import Counter
from skimage.color import deltaE_ciede2000, rgb2lab
from scipy.stats import zscore
from scipy.linalg import expm
from sklearn.linear_model import LinearRegression

from src.save_avg_rand_matrices import load_rand_poss
import src.distance_utils as sdu
import src.graph_utils as sgu
import src.mixed_model as smm

from src.config import PATHS


# General Helpers {{{


def str_to_list(val):
    """Convert csv strings back to list and arrays if possible."""
    try:
        if isinstance(val, float) and np.isnan(val):
            return []
        if isinstance(val, str):
            return ast.literal_eval(val)
        return val  # Return as-is if not a string
    except (SyntaxError, ValueError):
        return val


def match_or_nan(a, b):
    """Compare two values, return whether they are equal or NaN if either value is NaN."""
    if np.isnan(a) or np.isnan(b):  # Check if either value is NaN
        return np.nan
    return a == b


def subjs_with_incomplete_data(dt: pd.DataFrame(), atol: int, verbose=0,
                               excl_only_lower=True):
    """Generate list of subjects with incorrect trial number."""
    trialnbs = dt.groupby("subject_id").size().tolist()
    correct_trialnb, _ = Counter(trialnbs).most_common(1)[0]

    subjs_with_incorr_trialnb = []
    for subj, trialnb in dt.groupby("subject_id").size().items():
        is_close = np.isclose(trialnb, correct_trialnb, atol=atol)
        if not is_close:
            if not excl_only_lower or trialnb < correct_trialnb:
                subjs_with_incorr_trialnb.append((subj, trialnb))

    if verbose > 0:
        print(f"Correct trial number: {correct_trialnb}")
        print(f"Subjects with incompl. data: {len(subjs_with_incorr_trialnb)}")
        if verbose > 1:
            print(subjs_with_incorr_trialnb,
                  " --> Correct trial nb: ", correct_trialnb)

    return subjs_with_incorr_trialnb


def zscore_m(m: np.ndarray) -> np.ndarray:
    """Z-score a symmetric matrix across rows and columns."""
    assert np.all(m == m.T), "Matrix not symmetric."
    z_m = zscore(m.flatten()).reshape(m.shape)
    assert np.all(z_m == z_m.T), "Z-Matrix not symmetric."
    return z_m


# Get subject average distance matrices
def calc_mat_mean(ms, zscore_flag=False):
    """Calculate mean matrix and sort out infs."""
    # Ignoring matrices containing inf values
    # only necessary because some connections were missing in task4b
    ms = [m for m in ms if not np.isinf(m).any()]
    if zscore_flag:
        ms = [zscore_m(m) for m in ms]  # z score elements in matrices
    return np.mean(ms, axis=0)


def cluster_distance_matrix(
        clusters, n_nodes=None, *, within_dist=1,
        between_dist=9, one_indexed=False):
    """Build an N x N integer distance matrix from cluster membership lists.

    Returns
    -------
    D : (N, N) ndarray of int
        Symmetric distance matrix with zeros on the diagonal.
    """
    # Flatten all indices to infer N if needed
    all_idx = [i for cl in clusters for i in cl]
    if not all_idx and n_nodes is None:
        raise ValueError("Empty clusters and n_nodes=None: cannot infer matrix size.")

    if one_indexed:
        # convert to 0-based internally
        clusters_0 = [[i-1 for i in cl] for cl in clusters]
        max_idx = max(all_idx) - 1 if all_idx else -1
    else:
        clusters_0 = clusters
        max_idx = max(all_idx) if all_idx else -1

    N = n_nodes if n_nodes is not None else (max_idx + 1)
    if N <= 0:
        raise ValueError("Inferred N <= 0; check your inputs.")

    # Membership matrix M: shape (K, N); M[k, j] = 1 if node j in cluster k
    K = len(clusters_0)
    M = np.zeros((K, N), dtype=bool)
    for k, cl in enumerate(clusters_0):
        # keep only valid indices in range [0, N)
        cl = [j for j in cl if 0 <= j < N]
        if cl:
            M[k, cl] = True

    # Co-membership matrix B: B[i, j] = True if i and j share any cluster
    # (M.T @ M) gives counts of shared clusters; >0 yields boolean
    B = (M.T @ M) > 0

    # Distances: start with 'between', then set within where B (off-diagonal)
    D = np.full((N, N), int(between_dist), dtype=int)
    np.fill_diagonal(D, 0)
    # Set within distances for off-diagonal entries that share a cluster
    # (avoid touching diagonal again)
    within_mask = B & ~np.eye(N, dtype=bool)
    D[within_mask] = int(within_dist)

    # Symmetrize (safety) and return
    # D = (D + D.T) // 2
    return D


def calc_successor_m(A, gamma=0.1):
    """Calculate successor representation matrix (von Neumann series)."""
    I_m = np.eye(A.shape[0])
    inv_closed = np.linalg.inv(I_m - gamma * A)
    return inv_closed


# }}}
# Core Data Helpers {{{


def get_nth_dominant_color(image_path, nth=1):
    """Get Nth most frequent color from image.

    Read image from specified path, reshape it into list of RGB
    pixel values, and calculates frequency of each color in image.
    The Nth most frequent color is returned.
    """
    # Load image and convert to RGB
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Reshape to a list of pixels
    pixels = image.reshape(-1, 3)
    # Count unique colors
    counts = Counter(map(tuple, pixels))
    # Get Nth most common color
    dominant_color = counts.most_common(nth)[nth - 1][0]

    return dominant_color


def delta_e_similarity(color1, color2):
    """Calculate the color difference between two colors.

    Uses the CIEDE2000 formula.
    """
    lab1 = rgb2lab(np.array(color1).reshape(1, 1, 3) / 255.0)
    lab2 = rgb2lab(np.array(color2).reshape(1, 1, 3) / 255.0)

    return deltaE_ciede2000(lab1[0, 0], lab2[0, 0])


def get_color_dist_matrix(cols, rounding=2):
    """Calculate Color distance matrix from colors vector."""
    col_m = np.array(
        [
            [delta_e_similarity(cols[i], cols[j]) for j in range(len(cols))]
            for i in range(len(cols))
        ]
    )

    if rounding is not None:
        return np.round(col_m, rounding)
    else:
        return col_m


# }}}
# Task 3 Helpers {{{


def get_congr_relation(row, dist_m):
    """Calculate whether path 1 or path 2 is longer according to a given distance matrix."""
    pair_1 = row["pathpair_congrtest"][0]
    pair_2 = row["pathpair_congrtest"][1]
    dist_pair_1 = row[dist_m][pair_1[0], pair_1[-1]]
    dist_pair_2 = row[dist_m][pair_2[0], pair_2[-1]]

    # Return NaN if distances are the same
    if dist_pair_1 == dist_pair_2:
        return np.nan
    return dist_pair_1 < dist_pair_2


def first_last_elm(lst: list):
    """Get first and last element of a list."""
    return lst[0], lst[-1]


def calc_pp_diff(ls: list):
    """Subtract last from first element of list.

    (To calculate pathpair difference.)
    """
    if any(np.isinf(x) for x in ls):
        return np.nan

    return ls[-1] - ls[0]


def get_pathpair_dist(row, dist):
    """Calculate distance for specific pathpair."""
    left_path = first_last_elm(row["pathpair_congrtest"][0])
    right_path = first_last_elm(row["pathpair_congrtest"][1])

    dists = row.get(dist)

    if isinstance(dists, (dict, pd.Series)):
        return dists.get(left_path, np.nan), dists.get(right_path, np.nan)

    if isinstance(dists, np.ndarray):
        try:
            return dists[left_path], dists[right_path]
        except (IndexError, TypeError):
            print(f"IndexError, TypeError in {row[{dist}]}: {type(dists)}")
            print(dists)
            return np.nan, np.nan

    return np.nan, np.nan


def get_acc(response, pp_diff):
    """Score response based on pathpair difference to get accuracy."""
    if (response == 0 and pp_diff > 0) or (response == 1 and pp_diff < 0):
        return 1.0
    else:
        return 0.0


# }}}
# Task 4 Helpers {{{


def exp_weights(n_trials, decay=0.1):
    """Compute exponential decay weights for recency effect."""
    return np.exp(-decay * np.arange(n_trials - 1, -1, -1))


def weight_trials(group_series, e_type=None, weight_decay=0.1):
    """Weight node positions of each subject with exp. decay/growth function.

    group_series: trials grouped by subject.
    """
    w_poss = {}

    for key, df in group_series:
        df = np.array(df.tolist())

        # Compute weights efficiently
        if e_type == "exp_growth":
            weights = exp_weights(len(df), decay=weight_decay)[::-1]
        elif e_type == "exp_decay":
            weights = exp_weights(len(df), decay=weight_decay)
        else:
            weights = np.ones(len(df))

        # Use NumPy broadcasting instead of list comprehension
        pos_weights = np.ones_like(df) * weights[:, np.newaxis, np.newaxis]

        # Element-wise multiplication is now fully vectorized
        w_poss[key] = df * pos_weights

    return pd.Series(w_poss)


def avg_poss_trials_by_subjs(trial_poss):
    """Calculate mean of node positions over trials for each subject."""
    return pd.Series({subj: np.mean(pos, axis=0)
                      for subj, pos in trial_poss.items()})


def add_prime_columns(task_data, var_type, zscore_flag=True):
    """Process the task data for both rotational and unconstrained var_types, apply MLR, and combine the results."""
    def _process_task(var_type):
        """Process task data for a specific var_type."""
        columns = [
            "subject_id",
            "spd_m_flat", "eucd_m_flat",
            "subj_spd_m_flat", "subj_eucd_m_flat",
            "mds_spd_m_flat", "mds_subj_spd_m_flat",
        ]
        if var_type == 'unconstrained':
            columns.remove("eucd_m_flat")

        # Prepare regression dataset
        mm_data = smm.prepare_mm4_dt(task_data, zscore_flag=zscore_flag)
        # Apply MLR for the appropriate columns and add residuals to df
        mm_data["subj_eucd_prime_m_flat"] = run_mlr_per_subj(
            mm_data, ["avg_subj_eucd_m_flat"], "subj_eucd_m_flat",
            return_resid=True)
        mm_data["subj_eucd_all_prime_m_flat"] = run_mlr_per_subj(
            mm_data, ["avg_subj_eucd_all_m_flat"], "subj_eucd_m_flat",
            return_resid=True)

        return mm_data

    # Process rotational and unconstrained data and combine
    mm = _process_task(var_type)

    def _merge_subj_eucd_prime_matrices(task_data, mm, matrix_col):
        # Fill upper triangle and symmetrize
        matrix_df = (
            mm.groupby("subject_id")[matrix_col]
            .apply(sgu.fill_upper_triangle_no_diag)
            .apply(lambda m: m + m.T)
            .reset_index()
            .rename(columns={matrix_col: matrix_col.replace("_flat", "")})
        )
        # Aggregate flat data
        flat_df = (
            mm.groupby("subject_id")[matrix_col]
            .agg(list)
            .reset_index()
        )
        # Merge both into task_data
        task_data = pd.merge(task_data, matrix_df, on="subject_id", how="outer")
        task_data = pd.merge(task_data, flat_df, on="subject_id", how="outer")

        return task_data

    task_data = _merge_subj_eucd_prime_matrices(
        task_data, mm, "subj_eucd_prime_m_flat")
    task_data = _merge_subj_eucd_prime_matrices(
        task_data, mm, "subj_eucd_all_prime_m_flat")

    return task_data


# }}}
# Task 3_4 Helpers {{{

def run_mlr_per_subj(dt: pd.DataFrame(), X_labels: list, y_label: str,
                     return_resid=True, return_coefs=False):
    """Run multiple linear regression independently for all subject_ids in dataframe and get residuals."""
    residuals = []
    y_preds = []
    coefs = []

    for subj in dt.subject_id.unique():
        dd = dt[dt.subject_id == subj]
        # Define predictors and outcome
        X = dd[X_labels]
        y = dd[y_label]
        # Fit the model
        model = LinearRegression()
        model.fit(X, y)
        # Get residuals
        y_pred = model.predict(X)
        residuals.extend(y - y_pred)
        y_preds.extend(y_pred)
        coefs.append(model.coef_)

    if return_resid:
        return residuals
    if return_coefs:
        return np.array(coefs)
    return y_preds

# }}}


def load_core_dt(dt_path, var_type):
    """Load core data for all tasks of part 1 and 2 of the experimet."""
    core_dt = pd.read_csv(dt_path / "core_data.csv")

    # Convert csv strings to lists and arrays
    core_dt["node_positions"] = core_dt["node_positions"].apply(str_to_list)
    core_dt["node_order"] = core_dt["node_order"].apply(str_to_list)
    core_dt["adj_m"] = core_dt["adj_m"].apply(str_to_list).apply(np.array)
    core_dt["spd_m"] = core_dt["spd_m"].apply(str_to_list).apply(np.array)
    if var_type != "unconstrained":
        core_dt["posw_adj_m"] = core_dt["posw_adj_m"].apply(str_to_list).apply(np.array)
        core_dt["wspd_m"] = core_dt["wspd_m"].apply(str_to_list).apply(np.array)
        core_dt["eucd_m"] = core_dt["eucd_m"].apply(str_to_list).apply(np.array)
        core_dt["cosd_m"] = core_dt["node_positions"].apply(sdu.get_cosd_mat)
        core_dt["cosw_spd_m"] = core_dt["cosd_m"].apply(sdu.get_SPD_matrix)

    # Convert csv string to int (or nan)
    core_dt["age"] = core_dt["age"].apply(
        lambda x: int(x) if type(x) is int else np.nan
        # lambda x: np.nan if x == [] else int(x)
    )

    # Add color distance matrix
    def order_node_colors(node_order):  # a closure captures node_colors
        ord_colors = [node_colors[node_nb] for node_nb in node_order]
        return ord_colors

    node_colors = {
        nb: get_nth_dominant_color(PATHS["nodes"] / f"node{nb}.png", 2)
        for nb in range(1, 10)
    }
    core_dt["ordered_node_colors"] = core_dt["node_order"].apply(order_node_colors)
    core_dt["color_m"] = core_dt["ordered_node_colors"].apply(get_color_dist_matrix)

    # Clean Data frame by dropping helper columns
    core_dt = core_dt.drop(
        columns=[
            "ordered_node_colors",
        ]
    )

    return core_dt


def load_task1_dt(dt_path):
    """Load data of task1 in part 1 of the experimet."""
    task1_dt = pd.read_csv(dt_path / "task1_data.csv")

    columns_to_process = [
        "nodepos_learnanim",
        "nodepos_drawtest",
        "nodes_clicked_learnanim",  # NOTE: doesn't exist in batch1
        "attempts_drawtest",  # NOTE: doesn't exist in batch1
    ]
    for col in columns_to_process:
        if col in task1_dt.columns:
            task1_dt[col] = task1_dt[col].apply(str_to_list)
        else:
            task1_dt[col] = np.nan

    cols = ["nodes_clicked_learnanim"]
    for col in cols:
        def nc_len(x):
            if isinstance(x, float) and np.isnan(x):
                return np.nan
            return len(x)
        task1_dt[f"nb_{col}"] = task1_dt[col].apply(
            lambda x: len(x) if isinstance(x, list) else np.nan)

    # There is this weird error in the batch1_rotational data in that there
    # 62 trials in which nodepos_drawtest has only 3 positions, the
    # drawtest_eucd_m therefore is only (3, 3) which causes errors.
    # checking whether participant Qs9u9i32ww1j4k18vuzriicg7Q is in the data ensures matrices
    # are only set to nan for batch1_rotational data.
    if "Qs9u9i32ww1j4k18vuzriicg7Q" in task1_dt.subject_id.values:
        task1_dt = task1_dt[task1_dt["nodepos_drawtest"].apply(
            lambda x: len(x) != 3)]

    return task1_dt


def load_task2_dt(dt_path, verbose=0):
    """Load data of task2 in part 1 of the experimet."""
    task2_dt = pd.read_csv(dt_path / "task2_data.csv")

    task2_dt["pair_learnrelquest"] = \
        task2_dt["pair_learnrelquest"].apply(str_to_list)

    return task2_dt


def load_task3_dt(dt_path, var_type):
    """Load and ammend data of task3 in part 2 of the experimet."""
    # Load task 3 data
    task3_dt = pd.read_csv(dt_path / "task3_data.csv")

    # Convert csv strings to lists and arrays
    task3_dt["pathpair_congrtest"] = \
        task3_dt["pathpair_congrtest"].apply(str_to_list)

    # Additionally load core
    core_dt = load_core_dt(dt_path, var_type)

    # Merge with some core data
    task3_dt = pd.merge(
        task3_dt,
        core_dt[
            [
                "subject_id",
                "node_positions",
                "adj_m",
                "spd_m",
                "color_m",
            ]
        ],
        on="subject_id",
    )
    if var_type != "unconstrained":
        task3_dt = pd.merge(
            task3_dt,
            core_dt[["subject_id",
                     "eucd_m", "posw_adj_m", "wspd_m",
                     "cosd_m", "cosw_spd_m",
                     ]],
            on="subject_id",
        )

    # Add different congruencies based on EUCL dist (e), WSPD (w), and
    # combination where both are equally congruent or incongruent (a)
    # or where they both only congruent (x)
    task3_dt["spd_relation"] = task3_dt.apply(
        get_congr_relation, dist_m="spd_m", axis=1
    )
    if var_type != "unconstrained":
        task3_dt["wspd_relation"] = task3_dt.apply(
            get_congr_relation, dist_m="wspd_m", axis=1
        )
        task3_dt["eucd_relation"] = task3_dt.apply(
            get_congr_relation, dist_m="eucd_m", axis=1
        )

        task3_dt["eucd_congr"] = task3_dt.apply(
            lambda r: match_or_nan(r["spd_relation"], r["eucd_relation"]),
            axis=1)
        task3_dt["wspd_congr"] = task3_dt.apply(
            lambda r: match_or_nan(r["spd_relation"], r["wspd_relation"]),
            axis=1)

    # Calculate distances for paths in pathpairs
    task3_dt["spd_pp_dist"] = task3_dt.apply(get_pathpair_dist, args=("spd_m",), axis=1)
    task3_dt["color_pp_dist"] = task3_dt.apply(
        get_pathpair_dist, args=("color_m",), axis=1
    )
    if var_type != "unconstrained":
        task3_dt["wspd_pp_dist"] = task3_dt.apply(
            get_pathpair_dist, args=("wspd_m",), axis=1
        )
        task3_dt["eucd_pp_dist"] = task3_dt.apply(
            get_pathpair_dist, args=("eucd_m",), axis=1
        )
        task3_dt["cosd_pp_dist"] = task3_dt.apply(
            get_pathpair_dist, args=("cosd_m",), axis=1
        )
        task3_dt["cosw_spd_pp_dist"] = task3_dt.apply(
            get_pathpair_dist, args=("cosw_spd_m",), axis=1
        )

    # Calculate path pair difference between distances
    task3_dt["spd_pp_diff"] = task3_dt["spd_pp_dist"].apply(calc_pp_diff)
    task3_dt["color_pp_diff"] = task3_dt["color_pp_dist"].apply(calc_pp_diff)
    if var_type != "unconstrained":
        task3_dt["wspd_pp_diff"] = task3_dt["wspd_pp_dist"].apply(calc_pp_diff)
        task3_dt["eucd_pp_diff"] = task3_dt["eucd_pp_dist"].apply(calc_pp_diff)

    # # Log transform RTs
    # task3_dt["log_rt_congrtest"] = task3_dt["rt_congrtest"].apply(np.log)

    # Score responses based on other distances
    task3_dt["acc_spd"] = task3_dt.apply(
        lambda r: get_acc(r["response"], r["spd_pp_diff"]), axis=1
    )  # == "acc_congrtest"
    if var_type != "unconstrained":
        task3_dt["acc_eucd"] = task3_dt.apply(
            lambda r: get_acc(r["response"], r["eucd_pp_diff"]), axis=1
        )
        task3_dt["acc_wspd"] = task3_dt.apply(
            lambda r: get_acc(r["response"], r["wspd_pp_diff"]), axis=1
        )

    # Clean Data frame by dropping helper columns
    task3_dt = task3_dt.drop(
        columns=[
            "spd_pp_dist",
            "color_pp_dist",
        ]
    )
    if var_type != "unconstrained":
        task3_dt = task3_dt.drop(
            columns=[
                "wspd_pp_dist",
                "eucd_pp_dist",
            ]
        )

    return task3_dt


def avg_eucd_ms_learn_df(task1_dt, decay=None):
    """Create average eucd matrices of node positions of learning trials and weight them as a function of decay rate."""
    task1_dt["drawtest_eucd_m"] = (
        task1_dt["nodepos_drawtest"].apply(sdu.euclid_dist_matrix).transform(zscore_m)
    )
    task1_dt["learnanim_eucd_m"] = (
        task1_dt["nodepos_learnanim"].apply(sdu.euclid_dist_matrix).transform(zscore_m)
    )

    grouped_dt = task1_dt.groupby("subject_id")

    def mat_avg(ms):
        """Calculate column mean over matrices."""
        return np.mean(ms, axis=0)

    if decay is not None:
        decay_vals = [decay] * 6
        decay_vals[0] = None
        decay_vals[3] = None
    else:
        decay_vals = [None, 0.068, 0.492, None, 0.017, 0.813]
        # Values from "Fit Primacy and Recency Weights" notebook
    avg_eucd_ms_learn = (
        pd.DataFrame(
            {
                "avg_learnanim_eucd_m": weight_trials(
                    grouped_dt["learnanim_eucd_m"], None, decay_vals[0]
                ).apply(mat_avg),
                "priw_avg_learnanim_eucd_m": weight_trials(
                    grouped_dt["learnanim_eucd_m"], "exp_decay", decay_vals[1]
                ).apply(mat_avg),
                "recw_avg_learnanim_eucd_m": weight_trials(
                    grouped_dt["learnanim_eucd_m"], "exp_growth", decay_vals[2]
                ).apply(mat_avg),
                "avg_drawtest_eucd_m": weight_trials(
                    grouped_dt["drawtest_eucd_m"], None, decay_vals[3]
                ).apply(mat_avg),
                "priw_avg_drawtest_eucd_m": weight_trials(
                    grouped_dt["drawtest_eucd_m"], "exp_decay", decay_vals[4]
                ).apply(mat_avg),
                "recw_avg_drawtest_eucd_m": weight_trials(
                    grouped_dt["drawtest_eucd_m"], "exp_growth", decay_vals[5]
                ).apply(mat_avg),
            }
        )
        .rename_axis("subject_id")
        .reset_index()
    )
    avg_eucd_ms_learn["avg_learn_eucd_m"] = avg_eucd_ms_learn[
        ["avg_learnanim_eucd_m", "avg_drawtest_eucd_m"]
    ].apply(lambda s: s.mean(), axis=1).apply(lambda m: m - m.min())
    avg_eucd_ms_learn["priw_avg_learn_eucd_m"] = avg_eucd_ms_learn[
        ["priw_avg_learnanim_eucd_m", "priw_avg_drawtest_eucd_m"]
    ].apply(lambda s: s.mean(), axis=1).apply(lambda m: m - m.min())
    avg_eucd_ms_learn["recw_avg_learn_eucd_m"] = avg_eucd_ms_learn[
        ["recw_avg_learnanim_eucd_m", "recw_avg_drawtest_eucd_m"]
    ].apply(lambda s: s.mean(), axis=1).apply(lambda m: m - m.min())

    # Aggregate in dataframe
    avg_eucd_ms_learn = avg_eucd_ms_learn[
        [
            "subject_id",
            "avg_learn_eucd_m",
            "priw_avg_learn_eucd_m",
            "recw_avg_learn_eucd_m",
        ]
    ]

    ctrl_m = avg_eucd_ms_learn["avg_learn_eucd_m"].iloc[0]
    assert np.array_equal(ctrl_m, ctrl_m.T), "Matrix is not symmetric"
    # assert np.all(np.diag(ctrl_m) == 0), "No zero diagonal."

    return avg_eucd_ms_learn


def avg_pos_learn_ms_df(task1_dt, decay=None):
    """Average node positions of learning trials and weight as a function of the decay rate. Then create eucd matrices.

    Note: Don't zscore before averaging. This doesn't make sense
    for positions I think because participants don't z-score them.
    """
    grouped_dt = task1_dt.groupby("subject_id")
    if decay is not None:
        decay_vals = [None, decay, decay]
    else:
        # Values from "Fit Primacy and Recency Weights" notebook
        decay_vals = [None, 0.017, 0.814]
    avg_poss_df = pd.DataFrame(
        {
            "subject_id": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_drawtest"],
                              None, decay_vals[0])).index,
            "avg_pos_drawtest": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_drawtest"],
                              None, decay_vals[0])).values,
            "recw_avg_pos_drawtest": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_drawtest"],
                              "exp_decay", decay_vals[1])).values,
            "priw_avg_pos_drawtest": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_drawtest"],
                              "exp_growth", decay_vals[2])).values,
            "avg_pos_learnanim": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_learnanim"],
                              None, decay_vals[0])).values,
            "recw_avg_pos_learnanim": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_learnanim"],
                              "exp_decay", decay_vals[1])).values,
            "priw_avg_pos_learnanim": avg_poss_trials_by_subjs(
                weight_trials(grouped_dt["nodepos_learnanim"],
                              "exp_growth", decay_vals[2])).values,
        }
    )

    for d in ["avg_pos", "recw_avg_pos", "priw_avg_pos"]:
        # Get mean positions
        avg_poss_df[f"{d}_learn"] = avg_poss_df[
            [f"{d}_drawtest", f"{d}_learnanim"]
        ].apply(lambda s: s.mean(), axis=1)
        # Calculate distance matrices
        avg_poss_df[f"{d}_learn_m"] = avg_poss_df[f"{d}_learn"].apply(
            sdu.euclid_dist_matrix
        )

    return avg_poss_df


def load_task4_dt(dt_path, var_type, verbose=0):
    """Load task 4 data."""
    # Load data
    task1_dt = load_task1_dt(dt_path)
    task4_dt = pd.read_csv(dt_path / "task4_data.csv")

    # Convert csv strings to lists and arrays
    task4_dt["nodepos_spatialpos_norel"] = task4_dt["nodepos_spatialpos_norel"].apply(
        str_to_list
    )
    task4_dt["relations_spatialpos_rel"] = task4_dt["relations_spatialpos_rel"].apply(
        str_to_list
    )

    # Additionally load core data
    core_dt = load_core_dt(dt_path, var_type)

    # Merge with some core data
    task4_dt = (
        pd.merge(task4_dt, core_dt[["subject_id", "adj_m", "spd_m", "color_m"]])
        .drop_duplicates("subject_id")
        .reset_index(drop=True)
    )
    assert len(task4_dt.subject_id) == len(task4_dt), "Duplicate subjects."

    if var_type != "unconstrained":
        task4_dt = pd.merge(
            task4_dt,
            core_dt[["subject_id", "wspd_m", "eucd_m",
                     "cosd_m", "cosw_spd_m",
                     ]]
            .drop_duplicates("subject_id")
            .reset_index(drop=True),
        )

    # Rename some columns
    task4_dt.rename(
        columns={
            "nodepos_spatialpos_norel": "subj_pos",
            "relations_spatialpos_rel": "subj_relations",
        },
        inplace=True,
    )

    # Get subjective adjacency matrix
    try:
        task4_dt["subj_adj_m"] = task4_dt["subj_relations"].apply(
            lambda e: sgu.get_adj_matrix_from_edges(e, 8)
        )
    except ValueError:  # for pilot 6
        task4_dt["subj_adj_m"] = task4_dt["subj_relations"]

    # Get subject specific distance matrices
    task4_dt["subj_eucd_m"] = task4_dt["subj_pos"].apply(sdu.euclid_dist_matrix)
    task4_dt["subj_spd_m"] = task4_dt["subj_adj_m"].apply(sdu.get_SPD_matrix)
    task4_dt["subj_wadj_m"] = task4_dt.apply(
        lambda m: sdu.get_wadj_matrix(m["subj_adj_m"], m["subj_eucd_m"]), axis=1
    )
    task4_dt["subj_wspd_m"] = task4_dt["subj_wadj_m"].apply(sdu.get_SPD_matrix)

    task4_dt["subj_cosd_m"] = task4_dt["subj_pos"].apply(sdu.get_cosd_mat)
    task4_dt["subj_cosw_spd_m"] = task4_dt["subj_cosd_m"].apply(sdu.get_SPD_matrix)

    # Add MDS embedded SPD positions and Euclidean distanc matrices thereof
    task4_dt["mds_subj_spd_pos"] = task4_dt["subj_spd_m"].apply(sdu.run_mds)
    task4_dt["mds_spd_pos"] = task4_dt["spd_m"].apply(sdu.run_mds)
    task4_dt["mds_spd_m"] = task4_dt["mds_spd_pos"].apply(sdu.euclid_dist_matrix)
    task4_dt["mds_subj_spd_m"] = task4_dt["mds_subj_spd_pos"].apply(sdu.euclid_dist_matrix)

    avg_subj_spd_ms = []
    avg_subj_wspd_ms = []
    avg_subj_eucd_ms = []
    avg_subj_pos_eucd_ms = []
    for subj in task4_dt.subject_id:
        loo = task4_dt[task4_dt.subject_id != subj]  # leave subj-out
        # Calculate average subject distance matrices
        avg_subj_spd_ms.append(calc_mat_mean(loo["subj_spd_m"]))
        avg_subj_wspd_ms.append(calc_mat_mean(loo["subj_wspd_m"]))
        avg_subj_eucd_ms.append(calc_mat_mean(loo["subj_eucd_m"]))
        # Calculate average subject positiong distance matrices
        avg_sbj_pos = np.array(loo["subj_pos"].tolist()).mean(axis=0)
        avg_subj_pos_eucd_ms.append(sdu.euclid_dist_matrix(avg_sbj_pos))

    task4_dt["avg_subj_spd_m"] = avg_subj_spd_ms
    task4_dt["avg_subj_wspd_m"] = avg_subj_wspd_ms
    task4_dt["avg_subj_eucd_m"] = avg_subj_eucd_ms
    task4_dt["avg_subj_pos_eucd_m"] = avg_subj_pos_eucd_ms

    # Get full mean without leave-one out
    task4_dt["avg_subj_eucd_all_m"] = \
        [calc_mat_mean(task4_dt["subj_eucd_m"])] * len(task4_dt)

    # Get random distance matrices
    graph_id = "10248905"
    rand_avg_mats = np.load(PATHS["random_graphs"] / f"avg_rand_mats_{graph_id}.npz")
    for d in ["spd", "eucd", "wadj", "wspd"]:
        avg_rand_m = rand_avg_mats[f"avg_rand_{d}_m"]
        # Add matrix to data frame (same matrix in each row, as in your original code)
        task4_dt[f"avg_rand_{d}_m"] = [avg_rand_m] * len(task4_dt)

    # Get random position distance matrices
    avg_rand_poss = load_rand_poss(graph_id).mean(axis=0)
    avg_rand_poss_eucd_m = sdu.euclid_dist_matrix(avg_rand_poss)
    task4_dt["avg_rand_pos_eucd_m"] = [avg_rand_poss_eucd_m] * len(task4_dt)

    # Add (weighted) mean learning positions
    # ======================================
    # Create data frame of mean positions (no z-scoring)
    avg_poss_df = avg_pos_learn_ms_df(task1_dt)
    task4_dt = pd.merge(
        task4_dt,
        avg_poss_df,
        on="subject_id",
        how="outer",
    )

    # Add (weighted) mean distance matrices of learn positions
    # ========================================================
    # Get (weighted) mean of Euclidean distance matrices of learning trials.
    # Z-score matrices before, s.t. they have equal influence
    avg_eucd_ms_learn = avg_eucd_ms_learn_df(task1_dt)

    task4_dt = pd.merge(task4_dt, avg_eucd_ms_learn, on="subject_id", how="outer")

    # Add Euclidean graph layouts
    # ===========================
    adj_m = core_dt["adj_m"].iloc[0]
    G = nx.from_numpy_array(adj_m)
    linear_pos = {i: (i, 0) for i in range(len(G.nodes))}
    layouts = {
        "spring": nx.spring_layout,  # nearly same as spring layout
        "circular": nx.circular_layout,  # same as shell layout, similar to spiral layout
        "planar": nx.planar_layout,
        "linear": linear_pos,
    }
    layout_df = pd.DataFrame()
    seed_value = 3929
    for l_name, layout in layouts.items():
        if callable(layout):
            if "seed" in getattr(layout, "__code__", {}).co_varnames:
                pos = layout(G, seed=seed_value)
            else:
                pos = layout(G)  # circular layout does not have randomness
        else:
            pos = layout  # Use predefined layout (e.g., linear)
        layout_df[l_name + "_lay_pos"] = [list(pos.values())]

    for c in layout_df.columns:
        layout_df[f"{c[:-4]}_eucd_m"] = layout_df[c].apply(sdu.euclid_dist_matrix)
    layout_df = layout_df.loc[layout_df.index.repeat(len(task4_dt))].reset_index(drop=True)
    task4_dt = pd.concat([task4_dt, layout_df], axis=1)

    # Get centrality and communicability matrices
    commu_m = sgu.communicability_weight_matrix(adj_m)
    hub_norm_m = sgu.hub_normalized_weight_matrix(adj_m)
    task4_dt["hub_norm_m"] = [hub_norm_m] * len(task4_dt)
    task4_dt["communica_m"] = [commu_m] * len(task4_dt)
    # Get matrix exponential (Estrada and Hatano, 2008, 2010), see Garvert et al. 2017
    task4_dt["expo_m"] = [expm(adj_m)] * len(task4_dt)
    # Get cluster matrices
    clusters_1 = [[0, 1, 4, 7], [2, 3, 5, 6]]
    clusters_2 = [[0, 1, 4], [6, 7], [2, 3, 5]]
    clusters_3 = [[0, 1, 4, 2, 3, 5], [6, 7]]
    task4_dt["cluster1_m"] = [cluster_distance_matrix(clusters_1)] * len(task4_dt)
    task4_dt["cluster2_m"] = [cluster_distance_matrix(clusters_2)] * len(task4_dt)
    task4_dt["cluster3_m"] = [cluster_distance_matrix(clusters_3)] * len(task4_dt)
    # Get successor matrix
    task4_dt["successor_m"] = [calc_successor_m(adj_m, gamma=0.65)] * len(task4_dt)

    # Subtract Mean subjective Euclidean from Subjective Euclidean
    # ==========================
    def _zscore_and_subtract_m(r):
        from numpy.exceptions import AxisError
        try:
            # m = zscore(r["subj_eucd_m"]) - zscore(r["avg_subj_eucd_m"])
            m = r["subj_eucd_m"] - r["avg_subj_eucd_m"]
        except AxisError:  # catch nans
            m = r["subj_eucd_m"] - r["avg_subj_eucd_m"]
        return m

    task4_dt["subj_eucd_subt_m"] = task4_dt.apply(
        lambda r: _zscore_and_subtract_m(r), axis=1,
    )

    # Flatten all matrices in dt
    # ==========================
    m_columns = [col for col in task4_dt.columns if col.endswith("_m")]

    def safe_flatten(x):
        try:
            return sdu.flatten_tril_mat(x)
        except Exception as e:
            # print(f"Flattened matrix set to 0 because {e}")
            return [0]*28

    for col in m_columns:
        task4_dt[f"{col}_flat"] = task4_dt[col].apply(safe_flatten)

    # Add Prime columns
    # =================
    # task4_dt = add_prime_columns(task4_dt, var_type, zscore_flag=True)

    return task4_dt


def load_task3_and_4_dt(dt_path, var_type):
    """Load data for logLMM analysis of task 3."""
    # Load Task Data
    task3_dt = load_task3_dt(dt_path, var_type)
    task4_dt = load_task4_dt(dt_path, var_type)

    # Avoid the merger to use _x and _y endings for columns that are
    # in fact the same but not recognized as such because they are
    # arrays (but exclude subject_id columns).
    common_columns = task3_dt.columns.intersection(task4_dt.columns)
    common_columns = common_columns.drop("subject_id")
    task3_dt = task3_dt.drop(columns=common_columns)

    # Merge task 3 and matrices of task 4 dt
    task3_4_dt = pd.merge(
        task3_dt,
        task4_dt,
        on="subject_id",
    )

    # Calculate distances for paths in pathpairs, and pathpair differences
    # between distances for all matrix columns
    # m_columns = [col for col in task3_4_dt.columns if col.endswith("_m")]
    excl_cols = {"subj_adj_m", "adj_m", "posw_adj_m"}
    m_columns = [
        col for col in task3_4_dt.columns if col.endswith("_m")
        and col not in excl_cols
    ]
    dist_cols = {}
    diff_cols = {}

    cols_red = ['cosd_m', 'cosw_m', 'cosw_spd_m', 'spd_m',
                'color_m', 'wspd_m', 'eucd_m']
    m_cols_reduced = [col for col in m_columns if col not in cols_red]
    for col in m_cols_reduced:
        kn = f"{col[:-2]}_pp"
        # Compute the distance for the column
        dist_col = task3_4_dt.apply(get_pathpair_dist, args=(col,), axis=1)
        diff_col = dist_col.apply(calc_pp_diff)
        # Store in dictionaries
        dist_cols[f"{kn}_dist"] = dist_col
        diff_cols[f"{kn}_diff"] = diff_col
    # Combine all at once
    new_data = pd.DataFrame({**dist_cols, **diff_cols}, index=task3_4_dt.index)
    task3_4_dt = pd.concat([task3_4_dt, new_data], axis=1)

    # Definte Congruency in terms of subjective distances
    task3_4_dt["subj_eucd_relation"] = task3_4_dt.apply(
        get_congr_relation, dist_m="subj_eucd_m", axis=1)
    task3_4_dt["subj_eucd_congr"] = task3_4_dt.apply(
        lambda r: match_or_nan(r["spd_relation"], r["subj_eucd_relation"]),
        axis=1)

    # (Potentially) clean Data frame by dropping helper columns
    task3_4_dt = task3_4_dt.drop(
        task3_4_dt.filter(regex="_pp_dist$", axis=1).columns,
        axis=1
    )

    return task3_4_dt


def subjects_not_connect(dt, mm3=False):
    """Identify subjects who did not connect the graph in Task 4 (Arena task) or who did not participate in the task at all.

    This function checks for subjects in Task 4 whose spatial distance
    matrix (`subj_spd_m_flat`) contains infinite values (i.e.,
    indicating a failure in distance computation or connectivity).
    """
    if not mm3:
        dt = smm.prepare_mm3_dt(dt, zscore_flag=True)
    subjs_not_connect = dt[
        dt["subj_spd_pp_diff"].isna()]["subject_id"].unique()

    return subjs_not_connect


def get_cheaters(
        core_dt, cheaters=True, uncertains=True, #others=True,
        verbose=0):
    """Get all participants that answered 'Yes' or 'Sometimes' to the cheater question."""
    cheater_set = set()
    uncertain_set = set()
    other_set = set()

    if cheaters:
        cheater_set = set(
            core_dt.loc[core_dt["cheater"] == "Yes", "subject_id"])
    if uncertains:
        uncertain_set = set(
            core_dt.loc[core_dt["cheater"] == "Sometimes", "subject_id"])

    if verbose > 0:
        print(f"Cheaters: {len(cheater_set)}")
        print(f"Uncertains: {len(uncertain_set)}")
        # print(f"Others (incompl.): {len(other_set)}")

    # Return the union of the three sets
    return cheater_set | uncertain_set | other_set


def get_incompletes(core_dt, task2_dt, task3_dt, verbose=0):
    """Exclude participants with incomplete data.

    I.e. participants that did not complete part 1 or part 2.
    """
    core_ids = set(core_dt["subject_id"])
    task2_ids = set(task2_dt["subject_id"])
    task3_ids = set(task3_dt["subject_id"])

    # Participants without part 2 data but with part 1 data
    p1_but_not_p2 = task2_ids - task3_ids
    # Participants without part 1 data but with part 2 data
    p2_but_not_p1 = task3_ids - task2_ids
    # Participants in core_dt but neither in part 1 or 2 data
    c_but_not_p1orp2 = core_ids - (task3_ids | task2_ids)

    # NOTE on exclusions:
    # - The third condition is only for for one participant in batch2_unc
    # (Expt. 2) ('Qmtb1fu54zp4sdpnvvghg9tvtQ') who has a very small file of p1
    # - The second condition is only for one participants in batch1_rot
    # (Expt. 1) (Qz0ok7biq3oowh76c5bee68rbQ in batch 1 rotational. He/she
    # has part 2 fully complete but only did the 4 first trials in part 1:
    # 0       preload
    # 1       welcome
    # 2       consent
    # 3    fullscreen
    # 4           age
    # The justification for excluding this participant also for part 2 is
    # that I don't think the participant did part 1 but found a way to
    # get the completion code without doing the full task!
    # If I look at his/her free responses in task 3 and task 4 they both
    # say the same generic sentence:
    # 'visual memory with previous part in this study'
    # Not surprisingly he/she is also completely at chance in task 3 (52%).

    if verbose > 0:
        print(f"part 1 but not part 2: {len(p1_but_not_p2)}")
        if verbose > 1:
            print(" --- ", p1_but_not_p2)
        print(f"part 2 but not part 1: {len(p2_but_not_p1)}")
        if verbose > 1:
            print(" --- ", p2_but_not_p1)
        print(f"core dt but not part 1 nor 2: {len(c_but_not_p1orp2)}")
        if verbose > 1:
            print(" --- ", c_but_not_p1orp2)

    return p1_but_not_p2 | p2_but_not_p1 | c_but_not_p1orp2


def load_full_data(
    excl_cheaters=True,
    excl_uncertains=True,
    excl_incompl=True,
    verbose=2,
    var_types=["rotational", "unconstrained"],
):
    """Load full data and exclude participants."""
    batches = ["batch1", "batch2"]

    dt_names = ["core", "task1", "task2", "task3", "task4", "task3_4"]
    dt = {name: pd.DataFrame() for name in dt_names}

    for batch in batches:
        for var_type in var_types:
            fp = PATHS.get(batch + f"-tidy-{var_type}")
            if not fp or not fp.is_dir():
                continue

            if verbose > 1:
                print(f"Loading {batch}-{var_type}...")

            temp_dt = {}
            temp_dt["core"] = load_core_dt(fp, var_type)
            temp_dt["task1"] = load_task1_dt(fp)
            temp_dt["task2"] = load_task2_dt(fp, verbose=1)
            temp_dt["task3"] = load_task3_dt(fp, var_type)
            temp_dt["task4"] = load_task4_dt(fp, var_type)
            temp_dt["task3_4"] = load_task3_and_4_dt(fp, var_type)

            for dt_name in dt.keys():
                # Add batch and var type
                temp_dt[dt_name]["batch"] = batch
                temp_dt[dt_name]["var_type"] = var_type

                if dt_name in temp_dt and not temp_dt[dt_name].empty:
                    dt[dt_name] = pd.concat(
                        [dt[dt_name], temp_dt[dt_name]], ignore_index=True,
                    )

    # Filter core dataset to only include subjects present in any task
    task_subjs = set()
    for key in [k for k in dt_names if k != "core"]:
        task_subjs.update(dt[key]["subject_id"])
    dt["core"] = dt["core"][dt["core"]["subject_id"].isin(task_subjs)].copy()

    core_dt_rot = dt["core"].query("var_type == 'rotational'")
    core_dt_unc = dt["core"].query("var_type == 'unconstrained'")
    if verbose > 0:
        print("\nNb. Expt. 1 subjects before exclusion: "
              f"{len(core_dt_rot['subject_id'].drop_duplicates())}")
        print("\nNb. Expt. 2 subjects before exclusion: "
              f"{len(core_dt_unc['subject_id'].drop_duplicates())}")

    # Potentially exclude cheaters
    if verbose > 0:
        print("\nExcl. cheaters or uncertains in Expt. 1:")
    cheaters_rot = get_cheaters(
        core_dt_rot, excl_cheaters, excl_uncertains, verbose)
    if verbose > 0:
        print("\nExcl. cheaters or uncertains in Expt. 2:")
    cheaters_unc = get_cheaters(
        core_dt_unc, excl_cheaters, excl_uncertains, verbose)
    cheaters_all = cheaters_rot | cheaters_unc
    for dt_name in dt_names:
        dt[dt_name] = dt[dt_name][~dt[dt_name]["subject_id"].isin(cheaters_all)].copy()

    # Potentially exclude incompletes
    if excl_incompl:
        core_dt_rot = dt["core"].query("var_type == 'rotational'")
        task2_dt_rot = dt["task2"].query("var_type == 'rotational'")
        task3_dt_rot = dt["task3"].query("var_type == 'rotational'")
        if verbose > 0:
            print("\nExcluded incompletes in Expt. 1:")
        incompletes_rot = get_incompletes(
            core_dt_rot, task2_dt_rot, task3_dt_rot, verbose=verbose)

        core_dt_unc = dt["core"].query("var_type == 'unconstrained'")
        task2_dt_unc = dt["task2"].query("var_type == 'unconstrained'")
        task3_dt_unc = dt["task3"].query("var_type == 'unconstrained'")
        if verbose > 0:
            print("\nExcluded incompletes in Expt. 2:")
        incompletes_unc = get_incompletes(
            core_dt_unc, task2_dt_unc, task3_dt_unc, verbose=verbose)

        incompletes_all = incompletes_rot | incompletes_unc

        for dt_name in dt_names:
            dt[dt_name] = dt[dt_name][
                ~dt[dt_name]["subject_id"].isin(incompletes_all)].copy()

    return dt["core"], dt["task1"], dt["task2"], \
        dt["task3"], dt["task4"], dt["task3_4"]


if __name__ == "__main__":

    core_dt, task1_dt, task2_dt, task3_dt, \
        task4_dt, task3_4_dt = load_full_data()

    core_dt.to_csv(PATHS["augmented_data"] / "core_dt.csv", index=False)
    task1_dt.to_csv(PATHS["augmented_data"] / "task1_dt.csv", index=False)
    task2_dt.to_csv(PATHS["augmented_data"] / "task2_dt.csv", index=False)
    task3_dt.to_csv(PATHS["augmented_data"] / "task3_dt.csv", index=False)
    task4_dt.to_csv(PATHS["augmented_data"] / "task4_dt.csv", index=False)
    task3_4_dt.to_csv(PATHS["augmented_data"] / "task3_4_dt.csv", index=False)
