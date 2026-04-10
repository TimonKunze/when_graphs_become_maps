import os
import argparse
import itertools
import numpy as np
import pandas as pd
import networkx as nx

from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

import src.stat_utils as ssu
import src.graph_utils as sgu
import src.distance_utils as sdu
import src.opt_position_utils as sopu


def evaluate_chunk(chunk, adj_m, spd_m, G, min_nb_pairs, cross_allowed, touch_allowed, max_len_paths, corr_tol=None):
    results = []
    for pos in chunk:

        # 0. CONDITION
        # ------------
        # Check whether correlation between distance matrices is approximately equal
        # Maybe a difference in correlation of 10 is permissable
        corr_cond = True

        if corr_tol is not None:
            euc_m = sdu.euclid_dist_matrix(pos)
            wspd_m = sdu.get_SPD_matrix(adj_m * euc_m)
            spd_flat, wspd_flat, euc_flat = map(sdu.flatten_tril_mat, [spd_m, wspd_m, euc_m])
            corr_type = "spearman"
            corrs = [ssu.calc_correlation(spd_flat, wspd_flat, corr_type)[0],
                     ssu.calc_correlation(spd_flat, euc_flat, corr_type)[0],
                     ssu.calc_correlation(wspd_flat, euc_flat, corr_type)[0]]
            corr_cond = np.allclose(corrs, corrs[0], atol=corr_tol)

        if corr_cond:

            # 1. CONDITION
            # ------------
            # Check wether graph presentation contains touches or crossings
            # (i.e. if it is planar)
            touches, crosses = sopu.check_graphpos_planarity(G, pos)
            if (cross_allowed and touch_allowed) or \
            (cross_allowed and not touch_allowed and not touches) or \
            (touch_allowed and not cross_allowed and not crosses) or \
            (not cross_allowed and not touch_allowed and not crosses and not touches):

                # 2. CONDITION
                # ------------
                # Exclude rotationally or translationally identical
                # positions
                # unique_prev_graph_poss = []
                # for key in ["eucd", "wspd", "comb"]:
                #     unique_prev_graph_poss += graph_poss[key]
                # unique_prev_graph_poss = list(set(unique_prev_graph_poss))
                # # Delete duplicates
                # sim_pos_cond = sopu.similar_position_found(unique_prev_graph_poss, pos,
                #                                           env_size, grid_spacing)
                # if not sim_pos_cond:
                if True:

                    # Get distance matrices
                    euc_m = sdu.euclid_dist_matrix(pos)
                    wspd_m = sdu.get_SPD_matrix(adj_m * euc_m)

                    # Get congruent and incongruent pairs
                    congr = {}
                    incongr = {}
                    # For SPD-vs-EUCD
                    congr["eucd"], incongr["eucd"], *_ = sopu.get_congr_and_incongr_pairs(
                        adj_m, spd_m, euc_m, min_len_paths=3, nb_pairs=None, verbose=False,
                        max_len_paths=max_len_paths)
                    # For SPD-vs-wSPD
                    congr["wspd"], incongr["wspd"], *_ = sopu.get_congr_and_incongr_pairs(
                        adj_m, spd_m, wspd_m, min_len_paths=3, nb_pairs=None, verbose=False,
                        max_len_paths=max_len_paths)

                    # 3. CONDITION
                    # ------------
                    # Check that graph gives rise to suff. nb of congr/incongr pairs
                    min_nb_pairs_cond = len(congr["eucd"]) >= min_nb_pairs \
                                        and len(incongr["eucd"]) >= min_nb_pairs \
                                        and len(congr["wspd"]) >= min_nb_pairs \
                                        and len(incongr["wspd"]) >= min_nb_pairs
                    if min_nb_pairs_cond:

                        congr_diffs = {}
                        incongr_diffs = {}
                        congr_med = {}
                        incongr_med = {}
                        for key in ["eucd", "wspd"]:
                            # # Append number of congruent and incongruent pairs
                            # nb_congr[key].append(len(congr[key]))
                            # nb_incongr[key].append(len(incongr[key]))

                            # Add pair differences of congruent and incongruent
                            # pairs for the number of minimum pairs
                            congr_diffs[key] = [
                                sopu.pair_diff(congr[key][pair], euc_m, spd_m)
                                for pair in range(min_nb_pairs)]
                            incongr_diffs[key] = [
                                sopu.pair_diff(incongr[key][pair], euc_m, spd_m)
                                for pair in range(min_nb_pairs)]

                            # Get combination of pair differences by median (because
                            # it is less sensitive to outliers)
                            def combine_pairs(pairs):
                                return np.median(pairs)
                            congr_med[key] = combine_pairs(congr_diffs[key])
                            incongr_med[key] = combine_pairs(incongr_diffs[key])

                        # Get combination of pair difference medians for
                        # congr and incongr by taking the mean of the two values
                        def combine_pair_meds(meds):
                            return np.mean(meds)
                        congr_med["comb"] = combine_pair_meds([congr_med["eucd"],
                                                            congr_med["wspd"]])
                        incongr_med["comb"] = combine_pair_meds([incongr_med["eucd"],
                                                                incongr_med["wspd"]])

                        # 4. ORDERING
                        # -----------
                        # Insert new element in *ascendingly* ordered graph_positions
                        # Get insertion indices
                        med_objf = {}
                        med_list = {}
                        for key in ["eucd", "wspd", "comb"]:
                            # Maximize difference between congruent median and
                            # incongruent median
                            def objective_fun(congr_med, incongr_med):
                                return congr_med - incongr_med
                            med_objf[key] = objective_fun(congr_med[key],
                                                        incongr_med[key])

                            med_list[key] = [congr_med[key], incongr_med[key], med_objf[key]]

                        results.append([pos, med_list])
    
    return results


def chunkify_combinations(points, nb_nodes, chunk_size):
    """Generate chunks of combinations."""
    combinations = itertools.combinations(points, nb_nodes)
    while True:
        chunk = list(itertools.islice(combinations, chunk_size))
        if not chunk:
            break
        yield chunk


def run_full_graph_pos_optimization(
        grid_spacing, adj_m,
        cross_allowed=True, touch_allowed=True,
        min_nb_pairs=40, max_nb_pos=60, 
        weighted=True, save=True,
        chunk_size=1000, #1000
        max_workers=4,
        max_len_paths=None,
        corr_tol=None,
    ):

    # Fixed parameters

    # adj_m = np.array([ # 1870C0 in base16
    #     [0, 1, 1, 0, 0, 0, 0],
    #     [0, 0, 1, 1, 1, 0, 0],
    #     [0, 0, 0, 0, 0, 1, 1],
    #     [0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0],
    # ])
    # adj_m = adj_m + adj_m.T

    nb_nodes = np.shape(adj_m)[0]

    env_size = [900, 900]
    radius = env_size[0]/2 - 40
    center = (env_size[0]/2, env_size[1]/2)
    points = sopu.grid_points_in_circle(grid_spacing, center, radius)

    # Define binomial coefficient
    n = len(points)
    k = nb_nodes

    # Print runtime estimation
    sopu.print_combinatory_ETA(n, k)
    
    # Build nx graph
    G = nx.from_numpy_array(adj_m)

    # Get shortest path distance matrix
    spd_m = sdu.get_SPD_matrix(adj_m)
    
    # Initialize positions medians for combination, 
    # weighted and unweighted
    graph_poss = {}
    graph_meds = {}
    for key in ["eucd", "wspd", "comb"]:
        graph_poss[key] = [((0,0),)*k]*max_nb_pos
        graph_meds[key] = np.array([[0, 0, 0]]*max_nb_pos)

    # Loop through all possible positions
    # for pos in tqdm (itertools.combinations(points, k), desc="Running..."):
    print("Number of CPU cores on the machine: ", os.cpu_count())
    print("Number of max workers: ", max_workers)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(evaluate_chunk, chunk, \
                                   adj_m, spd_m, G, min_nb_pairs, \
                                   cross_allowed, touch_allowed, max_len_paths, corr_tol): chunk
                   for chunk in chunkify_combinations(points, nb_nodes, chunk_size)}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Running..."):
            results = future.result()
            for pos, med_list in results:
                for key in ["eucd", "wspd", "comb"]:

                    # Get Insert ind of med_objf
                    insert_ind = np.searchsorted(graph_meds[key][:, 2], 
                                                 med_list[key][2])
                    # Insert medians
                    graph_meds[key] = np.insert(graph_meds[key], 
                                                insert_ind, 
                                                med_list[key], axis=0)
                    # Insert position
                    graph_poss[key].insert(insert_ind, pos)
                    # Delete first element (to keep equal length)
                    graph_poss[key] = graph_poss[key][1:]
                    graph_meds[key] = graph_meds[key][1:]

    # Save as Dataframe
    dfs = []
    for key in ["eucd", "wspd", "comb"]:
        df = pd.DataFrame({
            "graph_poss": graph_poss[key],
            f"{key}_congru_med": graph_meds[key].T[0],
            f"{key}_inconr_med": graph_meds[key].T[1],
            f"{key}_ic_med_diff": graph_meds[key].T[2],
            #f"{key}_nb_congr": nb_congr[key],
            #f"{key}_nb_incongr": nb_incongr[key],
        })
        dfs.append(df)
        
    # Merge Dataframes and delete zero rows
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on="graph_poss", how="outer")
    merged_df.drop_duplicates(inplace=True)
    merged_df = merged_df[merged_df['graph_poss'] != ((0,0),)*k].reset_index(drop=True)
    merged_df["adj_m"] = [adj_m.tolist()] * len(merged_df)

    # Count non-zero entries and issue warning if zero
    count = len(merged_df)
    print(f"There are {count}/{max_nb_pos} found positions.")
    # print(f"The number of pairs are (mean/min/max): ")
    # print(f"- Eucd-Congrs: {.mean():.2f}/{np.array(nb_congrs).min()}/{np.array(nb_congrs).max()}")
    # print(f"- Eucd-Incongrs: {np.array(nb_incongrs).mean():.2f}/{np.array(nb_incongrs).min()}/{np.array(nb_incongrs).max()}")
    # print(f"- Wspd-Congrs: {np.array(nb_w_congrs).mean():.2f}/{np.array(nb_w_congrs).min()}/{np.array(nb_w_congrs).max()}")
    # print(f"- Wspd-Incongrs: {np.array(nb_w_incongrs).mean():.2f}/{np.array(nb_w_incongrs).min()}/{np.array(nb_w_incongrs).max()}")
    if count == 0:
        print("Alert: No positions found. Use different min_nb_pairs parameter!")

    if save:
        specs = (f"grid{grid_spacing}_min{min_nb_pairs}_max{max_nb_pos}"
                 f"_touch{touch_allowed}_cross{cross_allowed}_maxlenp{max_len_paths}_corrtol{corr_tol}")
        loc = "../data/generated_graph_positions/"
        b16_list = sgu.adjm_to_base16(adj_m)
        new_dir = os.path.join(loc, b16_list)
        os.makedirs(new_dir, exist_ok=True)
        merged_df.to_csv(os.path.join(new_dir, f'congr_opt_graph_pos_{specs}.csv'), index=False)
    return merged_df

    
# }}}

if __name__ == '__main__':
    """
    Run with:
    python run_congr_position_opt.py <grid_spacing_value> [--min-nb-pairs MIN_NB_PAIRS] [--max-nb-pos MAX-NB-POS] [--cross-allowed] [--touch-allowed]
    E.g.:
    python run_congr_position_opt.py 170 --min-pairs 1 --max-pairs 50 --cross-allowed --touch-allowed --save
    """

    parser = argparse.ArgumentParser(description='Search best graph positionings')
    parser.add_argument('grid_spacing', type=int, default=170, help='Grid spacing')
    parser.add_argument('hex_string', type=str, default="TBC", help='Hexadecimal string representing adj. matrix')
    parser.add_argument('--min-nb-pairs', type=int, default=1, help='Min nb congr/incongrpairs')
    parser.add_argument('--max-nb-pos', type=int, default=60, help='Max nb of stored positions')
    parser.add_argument('--cross-allowed', action='store_true', help='Crosses allowed')
    parser.add_argument('--touch-allowed', action='store_true', help='Touches allowed')
    parser.add_argument('--save', action='store_true', help='Save data as csv')
    parser.add_argument('--max-workers', type=int, default=10, help='Max number of kernels to use.')
    parser.add_argument('--max-len-paths', type=int, default=None, help='Max length of paths (currently either None or 4).')
    parser.add_argument('--corr-tol', type=int, default=None, help='The tolerance between correlations of dist matrices.')
    args = parser.parse_args()

    # Parameters
    adj_m = sgu.base16_to_adjm(args.hex_string)
    print(adj_m)
    
    run_full_graph_pos_optimization(
        args.grid_spacing, 
        adj_m,
        args.cross_allowed, 
        args.touch_allowed,
        min_nb_pairs=args.min_nb_pairs, 
        max_nb_pos=args.max_nb_pos,
        save=args.save,
        max_workers=args.max_workers,
        weighted=True, 
        max_len_paths=args.max_len_paths,
        corr_tol=args.corr_tol,
    )
