import os
import json
import argparse
import numpy as np
import networkx as nx

from tqdm import tqdm
from scipy.special import comb

import src.graph_utils as sgu
import src.distance_utils as sdu
import src.opt_position_utils as sopu

from src.config import PATHS



def run_position_sampling(
        adj_m,
        grid_spacing,
        cross_allowed,
        touch_allowed,
        max_nb_pos=1000,
        save=False,
    ):
    """Run a sampling for graph positions that ...
    """

    points = sopu.grid_points_in_circle(args.grid_spacing)

    nb_nodes = len(adj_m)
    spd_m = sdu.get_SPD_matrix(adj_m)
    comb_nb = int(comb(len(points), nb_nodes))

    print(f"Nb points: {len(points)}, Nb nodes: {nb_nodes}")
    print(f"Nb combinations: {comb_nb:,}")
    print(f"Run until: {max_nb_pos} positions found.")

    G = nx.from_numpy_array(adj_m)

    graph_poss = []

    # Run over random positionings
    for _ in tqdm(range(comb_nb)):
        if len(graph_poss) == max_nb_pos:
            break

        rand_inds = np.random.choice(range(len(points)), size=nb_nodes, replace=False)
        rand_pos = [points[ind] for ind in rand_inds]

        # MAYDO: Check whether graph presentation has same number of congruent and
        # incongruent trials of SPD and WSPD?

        # Check wether graph presentation contains touches or crossings
        # (i.e. if it is planar)
        touches, crosses = sopu.check_graphpos_planarity(G, rand_pos)
        if (cross_allowed and touch_allowed) or \
           (cross_allowed and not touch_allowed and not touches) or \
           (touch_allowed and not cross_allowed and not crosses) or \
           (not cross_allowed and not touch_allowed and not crosses and not touches):

            if rand_pos not in graph_poss:
                graph_poss.append(rand_pos)

    print(f"Number found positionings: {len(graph_poss)}")

    if save:
        specs = (f"grid{grid_spacing}_touch{touch_allowed}_cross{cross_allowed}")
        loc = PATHS["graph_pos_unconstr"]

        b16_list = sgu.adjm_to_base16(adj_m)
        new_dir = os.path.join(loc, b16_list)
        os.makedirs(new_dir, exist_ok=True)

        fp = os.path.join(new_dir, f'unconstr_graph_pos_{specs}.json')
        with open(fp, "w") as file:
            json.dump(graph_poss, file)

    return graph_poss


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(description='Sample graph positionings')
    parser.add_argument('graph_id', type=str, help='Graph ID')
    parser.add_argument('grid_spacing', type=int, help='Grid spacing')
    parser.add_argument('--cross-allowed', action='store_true', default=False, help='Cross allowed')
    parser.add_argument('--touch-allowed', action='store_true', default=False, help='Touch allowed')
    parser.add_argument('--save', action='store_true', help='Save data as npy')
    args = parser.parse_args()

    # Graph and Position Specs
    # graph_id = '10248905'
    graph_id = args.graph_id
    adj_m = sgu.base16_to_adjm(graph_id)

    varied_poss = run_position_sampling(
        adj_m=adj_m,
        grid_spacing=args.grid_spacing,
        cross_allowed=args.cross_allowed,
        touch_allowed=args.touch_allowed,
        save=args.save,
    )
