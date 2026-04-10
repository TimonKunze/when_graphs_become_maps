import os
import json
import argparse
import itertools
import numpy as np
import networkx as nx

from tqdm import tqdm
from scipy.special import comb
from concurrent.futures import ProcessPoolExecutor, as_completed

import src.graph_utils as sgu
import src.distance_utils as sdu
import src.opt_position_utils as sopu
import src.base_encodings as sbe

from src.config import PATHS


def check_pair_diff(pairs, d_m_ref, d_m_tar, spd_m, atol):
    """Compares the pair differences for a given set of pairs in a
    dictionary. Returns true if difference is found, otherwise false.

    Difference takes an absolute tolerance into account.
    """
    for pair in pairs:
        pd_tar = sopu.pair_diff(pair, d_m_tar, spd_m)
        pd_ref = sopu.pair_diff(pair, d_m_ref, spd_m)

        if not np.isclose(pd_tar, pd_ref, atol=atol):
            return True  # If any pair differs suff., return True
    return False  # If no suff. difference found, return False


def evaluate_chunk(chunk,
                   adj_m, spd_m, euc_m_ref, wspd_m_ref, pairs, G,
                   cross_allowed, touch_allowed, atol,
                   congr_type="a",
                   ):
    """Evaluates each target position in a chunk on whether there is a difference
    in distance, and if the graph positioning is planar. Only if no difference is
    found and is planar, gets the positioning saved.
    """
    results = []
    for pos_tar in chunk:
        # Check whether graph presentation has same distances (wspd + eucd)
        euc_m_tar = sdu.euclid_dist_matrix(pos_tar)
        wspd_m_tar = sdu.get_SPD_matrix(adj_m * euc_m_tar)

        if congr_type == "e" or congr_type == "a":
            if check_pair_diff(pairs["eCongr"], euc_m_ref, euc_m_tar, spd_m, atol):
                continue
            if check_pair_diff(pairs["eIncongr"], euc_m_ref, euc_m_tar, spd_m, atol):
                continue
        if congr_type == "w" or congr_type == "a":
            if check_pair_diff(pairs["wCongr"], wspd_m_ref, wspd_m_tar, spd_m, atol):
                continue
            if check_pair_diff(pairs["wIncongr"], wspd_m_ref, wspd_m_tar, spd_m, atol):
                continue

        # Check wether graph presentation contains touches or crossings
        # (i.e. if it is planar)
        touches, crosses = sopu.check_graphpos_planarity(G, pos_tar)
        if (cross_allowed and touch_allowed) or \
           (cross_allowed and not touch_allowed and not touches) or \
           (touch_allowed and not cross_allowed and not crosses) or \
           (not cross_allowed and not touch_allowed and not crosses and not touches):

            results.append(pos_tar)
    return results


def chunkify_combinations(combinations, points, nb_nodes, chunk_size):
    """Generate chunks of combinations."""
    while True:
        chunk = list(itertools.islice(combinations, chunk_size))
        if not chunk:
            break
        yield chunk


def run_vary_position_search(
        adj_m,
        pos_ref,
        pairs,
        grid_spacing,
        cross_allowed,
        touch_allowed,
        atol,
        chunk_size=100,
        max_workers=5,
        run_size=int(1.e8),
        congr_type="a",
        save=False,
    ):
    """Run a search for graph positions that ...
    """

    points = sopu.grid_points_in_circle(args.grid_spacing)
    nb_nodes = len(adj_m)
    spd_m, wspd_m_ref, euc_m_ref = sdu.get_dist_mats(pos_ref, adj_m)

    len_comb = comb(len(points), nb_nodes)
    print(f"Nb points: {len(points)}, Nb nodes: {nb_nodes}")
    print(f"Nb combinations: {len_comb:,}")

    # Build NX graph
    G = nx.from_numpy_array(adj_m)

    # Intialize positions and correlations
    graph_poss = [pos_ref]

    combinations = itertools.combinations(points, nb_nodes)

    break_loop = False
    run_size = int(run_size)
    nb_parts = int(np.ceil(len_comb/run_size))
    for part_i in range(nb_parts):
        print(f"Iteration: {part_i+1}/{nb_parts} (Max-len {run_size:,})")

        comb_iter = itertools.islice(
            combinations, part_i*run_size, part_i*run_size+run_size
        )

        # Run Parallelization
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(evaluate_chunk, chunk, \
                                    adj_m, spd_m, euc_m_ref, wspd_m_ref, pairs, G, \
                                       cross_allowed, touch_allowed, atol, congr_type): chunk
                    for chunk in chunkify_combinations(comb_iter, points, nb_nodes, chunk_size)}

            for future in tqdm(as_completed(futures), total=len(futures), desc="Running..."):
                try:
                    results = future.result()
                    for pos in results:
                        graph_poss.append(pos)
                        if len(graph_poss) > 5000:
                            break_loop = True
                            print("Break because more than 5000 results!")
                            break
                except Exception as e:
                    print(f"Task failed with exception: {e}")
                if break_loop:
                    break
            if break_loop:
                break

    print(f"Number found positionings: {len(graph_poss)-1}")

    if save:
        specs = (f"grid{grid_spacing}_atol{atol}_{congr_type}"
                 f"_touch{touch_allowed}_cross{cross_allowed}_{len(graph_poss)}")
        loc = PATHS["graph_pos_varied"]

        b16_list = sgu.adjm_to_base16(adj_m)
        pos_enc = sbe.encode_nested_numbers(pos)
        new_dir = os.path.join(loc, b16_list, pos_enc)
        os.makedirs(new_dir, exist_ok=True)

        fp = os.path.join(new_dir, f'varied_graph_pos_{specs}.json')
        with open(fp, "w") as file:
            json.dump(graph_poss, file)

    return graph_poss


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(description='Search best decorrelated graph positionings')
    parser.add_argument('grid_spacing', type=int, help='Grid spacing')
    parser.add_argument('--cross-allowed', action='store_true', default=False, help='Cross allowed')
    parser.add_argument('--touch-allowed', action='store_true', default=False, help='Touch allowed')
    parser.add_argument('--atol', type=int, default=1, help='Specify absolute tolerance')
    parser.add_argument('--max-workers', type=int, default=5, help='Max number of kernels to use.')
    parser.add_argument('--chunk-size', type=int, default=32000, help='Chunk size')
    parser.add_argument('--run-size', type=int, default=1.e8, help='Run size')
    parser.add_argument('--congr-type', type=str, default="a", help='e=Euclidean, w=wSPD, a=all')
    parser.add_argument('--save', action='store_true', help='Save data as npy')
    args = parser.parse_args()

    # Graph and Position Specs
    graph_id = '10248905'
    adj_m = sgu.base16_to_adjm(graph_id)
    pos_ref = [[220, 550], [220, 770], [440, 110], [440, 220], [550, 440], [660, 220], [770, 220], [770, 330]]
    pairs = {
        "eCongr": [[[5, 6, 7], [1, 7, 6, 5]], [[5, 6, 7], [1, 7, 6, 2]], [[1, 7, 6, 5], [0, 7, 1]], [[2, 6, 5, 3], [1, 7, 6, 5, 3]], [[1, 7, 6, 2], [0, 7, 1]], [[2, 6, 5], [1, 7, 6, 5]], [[4, 1, 7], [1, 7, 6, 5]], [[2, 6, 5], [1, 7, 6, 2]], [[4, 1, 7], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 5]], [[3, 5, 6], [1, 7, 6, 5]], [[3, 5, 6], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 2]], [[0, 7, 6, 5], [0, 7, 1]], [[2, 6, 7], [1, 7, 6, 5]], [[2, 6, 5], [0, 7, 6, 5]], [[4, 1, 7], [0, 7, 6, 5]], [[2, 6, 7], [1, 7, 6, 2]]],
        "eIncongr": [[[3, 5, 6], [4, 1, 7, 6]], [[2, 6, 5, 3], [5, 6, 7]], [[2, 6, 7], [3, 5, 6, 7]], [[0, 7, 1, 4], [2, 6, 7]], [[4, 1, 7, 6, 5], [4, 1, 7, 6]], [[1, 7, 6, 5], [1, 7, 6]], [[1, 7, 6, 2], [1, 7, 6]], [[2, 6, 7], [4, 1, 7, 6]], [[0, 7, 6, 5], [0, 7, 6]], [[0, 7, 6, 2], [0, 7, 6, 5, 3]], [[3, 5, 6, 7], [4, 1, 7, 6, 5]], [[2, 6, 7, 1, 4], [3, 5, 6, 7, 1, 4]], [[0, 7, 1, 4], [4, 1, 7, 6, 5]], [[1, 7, 6, 2], [1, 7, 6, 5, 3]], [[0, 7, 1], [2, 6, 5, 3]], [[1, 7, 6, 5, 3], [1, 7, 6, 5]], [[2, 6, 5, 3], [4, 1, 7]], [[2, 6, 5, 3], [2, 6, 5]]],
        "wCongr": [[[5, 6, 7], [0, 7, 1, 4]], [[3, 5, 6], [0, 7, 1, 4]], [[2, 6, 5], [0, 7, 1, 4]], [[2, 6, 7], [0, 7, 1, 4]], [[3, 5, 6, 7], [2, 6, 7, 1, 4]], [[0, 7, 6], [0, 7, 1, 4]], [[5, 6, 7], [4, 1, 7, 6]], [[2, 6, 7, 1, 4], [2, 6, 5, 3]], [[4, 1, 7, 6], [3, 5, 6]], [[3, 5, 6, 7], [4, 1, 7, 6, 5]], [[1, 7, 6], [0, 7, 1, 4]], [[5, 6, 7], [1, 7, 6, 2]], [[3, 5, 6], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 2]], [[4, 1, 7, 6], [2, 6, 5]], [[2, 6, 7], [4, 1, 7, 6]], [[0, 7, 6, 5], [2, 6, 7, 1, 4]], [[3, 5, 6], [0, 7, 6, 2]]],
        "wIncongr": [[[0, 7, 6, 5], [1, 7, 6]], [[1, 7, 6, 2], [4, 1, 7]], [[0, 7, 1], [4, 1, 7, 6]], [[1, 7, 6, 2], [1, 7, 6, 5, 3]], [[2, 6, 7, 1, 4], [3, 5, 6, 7, 1, 4]], [[2, 6, 7], [3, 5, 6, 7]], [[2, 6, 5], [3, 5, 6, 7]], [[0, 7, 6, 2], [0, 7, 6, 5, 3]], [[0, 7, 6], [2, 6, 5, 3]], [[0, 7, 6, 2], [4, 1, 7]], [[0, 7, 6, 5, 3], [1, 7, 6, 2]], [[0, 7, 1, 4], [2, 6, 7, 1, 4]], [[0, 7, 1], [1, 7, 6, 2]], [[1, 7, 6], [2, 6, 5, 3]], [[1, 7, 6, 5, 3], [4, 1, 7, 6]], [[0, 7, 1], [0, 7, 6, 2]], [[1, 7, 6, 5], [4, 1, 7]], [[0, 7, 6, 5, 3], [4, 1, 7, 6]]],
    }

    varied_poss = run_vary_position_search(
        adj_m=adj_m,
        pos_ref=pos_ref,
        pairs=pairs,
        grid_spacing=args.grid_spacing,
        cross_allowed=args.cross_allowed,
        touch_allowed=args.touch_allowed,
        atol=args.atol,
        max_workers=args.max_workers,
        chunk_size=args.chunk_size,
        run_size=args.run_size,
        congr_type=args.congr_type,
        save=args.save,
    )
