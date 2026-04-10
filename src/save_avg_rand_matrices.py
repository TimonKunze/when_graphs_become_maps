#!/usr/bin/env python3
import ast
import numpy as np
import pandas as pd
import json

import src.graph_utils as sgu
import src.distance_utils as sdu

from src.config import PATHS


def load_rand_poss(graph_id, grid=110):
    """Load random positions."""
    fp = (
        PATHS["graph_pos_unconstr"]
        / graph_id
        / f"unconstr_graph_pos_grid{grid}_touchFalse_crossFalse"
    )
    with open(fp.with_suffix(".json"), "r") as f:
        rand_poss = json.load(f)

    return np.array(rand_poss)


def load_matrices_from_txt(fp):
    """Loads a list of matrices from a text file, where each line contains a matrix
    represented in a Python list-of-lists format (e.g., `[[1,1,1],[2,2,2],[3,3,3]]`).
    """
    with open(fp, 'r') as file:
        lines = file.readlines()

    matrices = []
    for line in lines:
        matrix = ast.literal_eval(line.strip())
        matrices.append(np.array(matrix))

    return matrices


def load_rand_mats(graph_id, max_len=500):
    """Load random distance matrices (adj, wadj, spd, wspd, eucd)."""
    # 500 is max
    adj_m = sgu.base16_to_adjm(graph_id)

    # Get random distribution of adjacency and spd matrices
    nb_nodes = len(adj_m)
    nb_nodes = adj_m.shape[0]
    nb_edges = int(np.sum(adj_m) / 2)
    only_unique_sp = True
    only_isomorphs = False

    fn_adj_ms = (
        PATHS["random_graphs"]
        / f"rand_adj_ms_{nb_nodes}n_{nb_edges}e_uniqsp{only_unique_sp}_isom{only_isomorphs}.txt"
    )
    fn_spd_ms = (
        PATHS["random_graphs"]
        / f"rand_spd_ms_{nb_nodes}n_{nb_edges}e_uniqsp{only_unique_sp}_isom{only_isomorphs}.txt"
    )

    rand_adj_ms = load_matrices_from_txt(fn_adj_ms)
    rand_spd_ms = load_matrices_from_txt(fn_spd_ms)

    # Get random positions
    rand_poss = load_rand_poss(graph_id)

    # Get random distribution of distance matrices
    eucd_ms = [sdu.euclid_dist_matrix(pos, rounding=None) for pos in rand_poss]
    wadj_ms = [sdu.get_wadj_matrix(adj_m, eucd_m) for eucd_m in eucd_ms]
    wspd_ms = [sdu.get_SPD_matrix(wadj_m) for wadj_m in wadj_ms]

    rand_ms = pd.DataFrame(
        {
            "adj": rand_adj_ms[:max_len],
            "spd": rand_spd_ms[:max_len],
            "eucd": eucd_ms[:max_len],
            "wadj": wadj_ms[:max_len],
            "wspd": wspd_ms[:max_len],
        }
    )

    return rand_ms


def compute_and_save_avg_rand_mats(graph_id, max_len=500, out_path=None):
    # Get random distance matrices
    rand_ms = load_rand_mats(graph_id, max_len=max_len)

    avg_rand_mats = {}

    for d in ["spd", "eucd", "wadj", "wspd"]:
        # Take average
        # rand_ms[d] = rand_ms[d].transform(zscore_m)  # potentially zscore before
        avg_rand_m = rand_ms[d].mean()
        avg_rand_m -= avg_rand_m.min()  # ensure 0s on diagonal

        # Ensure that matrix is symmetric
        assert np.all(avg_rand_m == avg_rand_m.T), "Matrix not symmetric!"
        assert np.all(np.diag(avg_rand_m) == 0), "No zero diagonal."

        avg_rand_mats[f"avg_rand_{d}_m"] = avg_rand_m

    # Default file name if not provided
    if out_path is None:
        out_path = f"avg_rand_mats_{graph_id}.npz"

    # Save all matrices into a single compressed npz file
    np.savez(out_path, **avg_rand_mats)

    return out_path


if __name__ == "__main__":
    graph_Id = "10248905"
    avg_rand_file = compute_and_save_avg_rand_mats(
        graph_Id, max_len=500,
        out_path=PATHS["random_graphs"] / f"avg_rand_mats_{graph_Id}.npz"
    )
