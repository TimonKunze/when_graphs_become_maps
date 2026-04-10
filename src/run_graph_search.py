import math
import json
import gc
import argparse
import itertools
import numpy as np
import pandas as pd
import networkx as nx

from tqdm import tqdm
from collections import defaultdict
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from sklearn.manifold import MDS
from typing import Dict, List, Tuple, Any

from src.config import PATHS
import src.distance_utils as sdu

# Helpers {{{


def count_chunks(N, nb_edges, chunk_size):
    """Count the number of required chunks."""
    # N = nb_nodes * (nb_nodes - 1) // 2
    total_combinations = math.comb(N, nb_edges)
    num_chunks = (total_combinations + chunk_size - 1) // chunk_size
    # with integer ceiling

    return num_chunks


def binary_list_to_graph(bin_list, num_nodes):
    """Construct nx graph from binary list."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))

    idx = 0
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if bin_list[idx] == 1:
                G.add_edge(i, j)
            idx += 1

    return G


def extract_path_ends(paths):
    """Gather first and last elements from each path."""
    return [node for path in paths for node in (path[0], path[-1])]


def approximately_equal(a, b, tolerance):
    """Check whether two numbers are equal given some tolerance."""
    return abs(a-b) <= tolerance


def has_global_cycle(G):
    """Check whether graphs has global cycle (cycle involving all nodes)."""
    try:
        cycle = nx.find_cycle(G, orientation='original')
        # Check if the cycle includes all nodes in the graph
        cycle_nodes = {node for edge in cycle for node in edge[:2]}
        return len(cycle_nodes) == len(G.nodes)
    except nx.NetworkXNoCycle:
        return False  # No cycle found


def get_all_shortest_paths(G):
    """Return a dictionary of all shortest paths between all pairs of nodes in G."""
    all_paths = {}
    nodes = list(G.nodes())

    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if u != v:
                try:
                    paths = list(nx.all_shortest_paths(G, source=u, target=v,
                                                       weight="weight"))
                    all_paths[(u, v)] = paths
                except nx.NetworkXNoPath:
                    all_paths[(u, v)] = []

    return all_paths


def get_paths_of_length(
    all_paths: Dict[Tuple[Any, Any], List[List[Any]]],
    length: int
) -> List[List[Any]]:
    """Return a list of all paths with exactly the given length.

    Parameters:
        all_paths: dict mapping (source, target) to list of paths (each path is a list of nodes)
        length: desired path length (number of nodes in the path)

    Returns:
        List of paths (each path is a list) with exactly 'length' nodes.
    """
    return [p for paths in all_paths.values() for
            p in paths if len(p) == length]


def calc_mds_and_stress(dist_m: np.ndarray, num_dim=2) -> float:
    """Compute relative stress for a fitted MDS model from a distance matrix.

    Parameters:
    - mds: A fitted sklearn.manifold.MDS instance (with attribute `.stress_`)
    - dist_matrix: The original distance (dissimilarity) matrix, numpy array
        (square, symmetric)

    Returns:
    - relative_stress: float, normalized stress value (lower is better)
    """
    mds = MDS(num_dim, metric=True, dissimilarity='precomputed',
              random_state=42, n_init=1,
              # normalized_stress=True, # not supported for metric mds
              )
    # By default, metric MDS returns raw stress while non-metric
    # MDS returns normalized stress.
    embedding = mds.fit_transform(dist_m)  # embedding not used

    # relative_stress = mds.stress_
    raw_stress = mds.stress_
    # Sum squared distances only once (upper triangle, excluding diagonal)
    sum_squared_d = np.sum(dist_m ** 2) / 2  # since symmetric matrix
    relative_stress = np.sqrt(raw_stress / sum_squared_d)

    return embedding, relative_stress


def graph_invariant_key(G):
    """Generate a hashable invariant key.

    A graph invariant key is a value (or a combination of values)
    computed from a graph that remains unchanged under graph isomorphism.
    In other words, if two graphs are isomorphic (i.e., structurally
    identical), they will have the same invariant key.
    """
    degree_seq = tuple(sorted(dict(G.degree()).values()))
    num_edges = G.number_of_edges()

    return degree_seq, num_edges

# }}}
# Graph Search {{{

def check_path_end_overlap(all_paths, length_1, length_2):
    """Check if the sets of path endpoints for two path lengths are the same.

    Parameters:
        all_paths (dict): Dictionary of all shortest paths by (u, v).
        length_1 (int): First path length to compare.
        length_2 (int): Second path length to compare.

    Returns:
        bool: True if the sets of path ends are identical, False otherwise.
    """
    ends_1 = Counter(
        extract_path_ends(get_paths_of_length(all_paths, length_1))
    )
    ends_2 = Counter(
        extract_path_ends(get_paths_of_length(all_paths, length_2))
    )

    return set(ends_1) == set(ends_2)


def count_path_lengths(all_paths, lengths):
    """Count the number of paths of specific lengths.

    Parameters:
        all_paths (dict): Dictionary of all shortest paths by (u, v).
        lengths (list[int]): List of two path lengths to count.

    Returns:
        tuple: Count of paths of lengths lengths[0] and lengths[1].
    """
    counts = {lx: 0 for lx in lengths}
    for paths in all_paths.values():
        for p in paths:
            L = len(p)
            if L in counts:
                counts[L] += 1
    return counts[lengths[0]], counts[lengths[1]]


def compute_spd_embedding_correlation(spd_m):
    """Compute correlation between SPD matrix and MDS embedding distances."""
    pos = sdu.run_mds(spd_m, nb_dim=2, n_init=4)
    mds_spd = sdu.euclid_dist_matrix(pos)

    return np.corrcoef(
        sdu.flatten_tril_mat(spd_m),
        sdu.flatten_tril_mat(mds_spd)
    )[0, 1]


def evaluate_chunk(chunk, nb_nodes, min_nb_pathpairs=30, tol=4, no_corr_crit=False):
    """Evaluate a chunk of graphs based on structural and path-based constraints."""

    results = []
    seen_invariants = set()

    # Initialize filtered stats
    filtered = {
        "connected": 0,
        "invariance": 0,
        "min3times4": 0,
        "equal3and4": 0,
        "noend3and4": 0,
        "3and4suniq": 0,
        "3and4equal": 0,
        "correl<0.7": 0,
    }

    for binary_list in chunk:
        # 0.a filter: graph should be connected
        G = binary_list_to_graph(binary_list, nb_nodes)
        if not nx.is_connected(G):
            filtered["connected"] += 1
            continue

        # 0.a filter: graph should be invariant to earlier processed graphs
        key = graph_invariant_key(G)
        if key in seen_invariants:
            filtered["invariance"] += 1
            continue
        seen_invariants.add(key)

        spd_m = sdu.get_SPD_matrix_from_G(G)

        # 1.a filter: at least nb_3*nb_4 unique paths
        value_counts = dict(zip(*np.unique(spd_m, return_counts=True)))
        val3 = value_counts.get(3, 0)
        val4 = value_counts.get(4, 0)

        if val3 * val4 < min_nb_pathpairs:
            filtered["min3times4"] += 1
            continue

        # 1.b filter: nb_3 and nb_4 should be approximately equal
        if not approximately_equal(val3, val4, tol):
            filtered["equal3and4"] += 1
            continue

        # 2. filter: no missing path_ends for paths of len 3 and 4
        all_paths = get_all_shortest_paths(G)
        if not check_path_end_overlap(all_paths, length_1=3, length_2=4):
            filtered["noend3and4"] += 1
            continue

        # 3. filter: paths of length 3 or higher should be unique and
        # value counts should still > 30
        count_eq_3, count_eq_4 = count_path_lengths(all_paths, [4, 5])  # len(path) == nodes
        if count_eq_3 * count_eq_4 < min_nb_pathpairs:
            filtered["3and4suniq"] += 1
            continue
        if not approximately_equal(count_eq_3, count_eq_4, tol):
            filtered["3and4equal"] += 1
            continue

        # 4. filter: correlation should be lower than .75
        corr = compute_spd_embedding_correlation(spd_m)
        if no_corr_crit:
            if corr > 0.7:
                filtered["correl<0.7"] += 1
                continue

        results.append({
            "adj_m": nx.to_numpy_array(G).tolist(),
            "corr_spd": corr,
            # "invariant_key": key,
            # "nb_p_len3": count_eq_3,
            # "nb_p_len4": count_eq_4,
        })

    return results, filtered


def all_valid_binary_combinations(N, nb_edges):
    """Generate all binary lists of length N with exactly nb_edges ones."""
    for indices in itertools.combinations(range(N), nb_edges):
        bin_list = [0] * N
        for i in indices:
            bin_list[i] = 1
        yield bin_list


def chunkify(generator, chunk_size, num_chunks):
    """Yield successive chunks from a generator."""
    chunk_id = 0
    while True:
        chunk = list(itertools.islice(generator, chunk_size))
        if not chunk:
            break

        print(f"Processing chunk #{chunk_id:,}/{num_chunks:,}", flush=True)
        yield chunk
        chunk_id += 1


filtered = {
    "connected": 0,
    "invariance": 0,
    "min3times4": 0,
    "equal3and4": 0,
    "noend3and4": 0,
    "3and4suniq": 0,
    "3and4equal": 0,
    "correl<0.7": 0,
}

def run_graph_search(nb_nodes, nb_edges, max_workers=4,
                     chunk_size=9000, verbose=True, 
                     no_corr_crit=False, 
                     save=False):
    """Run graph search for specific number of nodes and edges."""
    # Length of binary list representing uppper triangle of adjacency matrix
    # without the diagonal

    N = int(nb_nodes*(nb_nodes-1)/2)
    N_valid = math.comb(N, nb_edges)
    if verbose:
        print(f"Nb nodes: {nb_nodes}")
        print(f"Nb edges: {nb_edges}")
        print(f"Nb elmnts in up. triangle of adj. m.: N={N}")
        # print(f"Nb all possible graphs under no constraint: 2^N=2^{N}={2**N:,}")
        print(f"Nb possible graphs under edge-nb-constraint: {N_valid:,}")

    full_res = []
    total_filtered = Counter()

    valid_combinations = all_valid_binary_combinations(N, nb_edges)

    num_chunks = count_chunks(N, nb_edges, chunk_size)
    chunked_generator = chunkify(valid_combinations, chunk_size, num_chunks)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # futures = []
        futures = set()
        for chunk in chunked_generator:
            future = executor.submit(evaluate_chunk, chunk, nb_nodes, no_corr_crit)
            # futures.append(future)
            futures.add(future)

            # Optionally limit how many futures are pending at once
            if len(futures) >= max_workers:
                done, futures = wait(futures, return_when=FIRST_COMPLETED)
                for completed in done:
                    results = completed.result()
                    results, filtered = results
                    for result in results:
                        full_res.append(result)
                    total_filtered.update(filtered)
                gc.collect()

        # Process any remaining futures
        for future in futures:
            results = future.result()
            results, filtered = results
            for result in results:
                full_res.append(result)
            total_filtered.update(filtered)
        gc.collect()

    print(f"--> Nb found graphs, 1st round: {len(full_res)}")

    # Step 1: Preprocess all graphs once
    graphs_with_keys = []
    for result in tqdm(full_res, desc="Preprocess all graphs..."):
        adj_m = np.array(result["adj_m"])
        G = nx.from_numpy_array(adj_m, create_using=nx.DiGraph)
        key = graph_invariant_key(G)  # You must define this
        graphs_with_keys.append((G, key, result))

    # Step 2: Group by invariant key
    buckets = defaultdict(list)
    for G, key, result in tqdm(graphs_with_keys,
                               desc="Group by invariant key..."):
        buckets[key].append((G, result))

    # Step 3: Within each bucket, deduplicate with early rejection
    full_res_2 = []
    for group in tqdm(buckets.values(), desc="Deduplicate..."):
        seen_graphs = []
        for G, result in group:
            is_duplicate = False
            for G_seen in seen_graphs:
                if not nx.faster_could_be_isomorphic(G, G_seen):
                    continue  # Definitely not isomorphic, skip expensive check
                if nx.is_isomorphic(G, G_seen):
                    is_duplicate = True
                    break
            if not is_duplicate:
                seen_graphs.append(G)
                full_res_2.append(result)

    print(f"--> Nb found graphs, 2nd round: {len(full_res_2)}")

    total_filtered_normalized = {k: np.round(v / N_valid, 4)
                                 for k, v in total_filtered.items()}

    if save:
        try:
            fn = (f"graphsearch_nbnodes{nb_nodes:02d}_nbedges{nb_edges:02d}"
                  f"_nbgraphs{len(full_res_2):05d}_nocorr{no_corr_crit}.json")
            fp = PATHS["graphs_corr"] / fn
            df = pd.DataFrame(full_res_2)
            df.to_json(fp, orient="records", lines=True)

            
            with open(PATHS["graphs_corr"] /
                      f"graphsearch_stats_nbnodes{nb_nodes:02d}_nbedges{nb_edges:02d}_nocorr{no_corr_crit}",
                      "w") as f:
                json.dump({"filtered": total_filtered,
                           "filtered_norm": total_filtered_normalized},
                          f, indent=4)

            print(f"Data successfully saved to {fp}")

        except (TypeError, IOError) as e:
            print(f"An error occurred while saving the file: {e}")

    print("Exclusion Stats:")
    print(total_filtered_normalized)
    print("")
    print(total_filtered)

    return full_res_2


# }}}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run graph search.')
    parser.add_argument('nb_nodes', type=int, help='Number of nodes')
    parser.add_argument('nb_edges', type=int, help='Number of edges')
    parser.add_argument('--chunk_size', type=int, default=50000, help='Size of chunks')
    parser.add_argument('--max-workers', type=int, default=8,
                        help='Max nb of workers')
    parser.add_argument('--no-corr-crit', action="store_true",
                        help='Do not include correlation criterium for exclusion')
    parser.add_argument('--save', action='store_true',
                        help='Save data as jsonl')
    args = parser.parse_args()

    full_results = run_graph_search(
        args.nb_nodes, args.nb_edges, args.max_workers,
        args.chunk_size, 
        no_corr_crit=args.no_corr_crit, save=args.save,
    )

