import scipy
import heapq
import numpy as np
import networkx as nx

from sklearn.manifold import MDS
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics.pairwise import cosine_distances

# Euclidean distances & matrices {{{


def euclid_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return np.linalg.norm(np.array(p1) - np.array(p2))


def euclid_dist_matrix(pos, rounding=None):
    """Calculate Euclidean distance matrix using SciPy's pdist.

    Note: Very fast and memory sufficient because it only computes the
    upper triangle and then mirrors the lower.
    """
    # Most memory efficient
    pos = np.array(pos)
    dist_matrix = squareform(pdist(pos, metric="euclidean"))

    if rounding is not None:
        return np.round(dist_matrix, rounding)
    return dist_matrix


def get_wadj_matrix(adj_m, euc_m):
    """Calculate weighted adjacency matrix."""
    return np.array(adj_m) * np.array(euc_m)


# }}}
# Shortest Path distance {{{


def find_paths(adj_matrix, start, end, visited=None, path=None):
    """Find all possible paths in an adjacency matrix using depth-first search.

    Parameters:
        adj_matrix (list of lists): Adjacency matrix representing the graph.
        start (int): The index of the starting node.
        end (int): The index of the ending node.
        visited (list): Keeps track of visited nodes to avoid cycles.
        path (list): Current path being explored.

    Returns:
        list of lists: List of paths from start to end.
    """
    if visited is None:
        visited = []
    if path is None:
        path = []

    visited.append(start)
    path = path + [start]

    if start == end:
        return [path]

    paths = []
    for i in range(len(adj_matrix[start])):
        if adj_matrix[start][i] >= 1 and i not in visited:
            new_paths = find_paths(adj_matrix, i, end, visited[:], path[:])
            for new_path in new_paths:
                paths.append(new_path)

    return paths


def get_unique_paths_of_minL(adj_m, min_length, non_unique_alert=True):
    """Return a list of unique and non-unique paths with short path
    distance. Works for unweighted and weighted adjacency matrix.

    Parameters:
        adj_m (np.matrix): unweighted or weighted adjacency matrix
        min_length (int): minimum STP
    Returns:
        two lists of SPD with unique paths and non-unique paths (the
        latter can be empty)
    """
    # Get all shortest unique paths for adjacency matrix
    unique_paths = []
    for i in range(len(adj_m)):
        for j in range(len(adj_m)):
            paths = find_paths(adj_m, i, j)
            if paths != []:
                # Get shortest paths
                minL = min(len(path) for path in paths)
                # Determine if path is unique
                minL_path = [p for p in paths if len(p) == minL]
                # Append
                unique_paths.append(minL_path)
            else:
                break

    # Check for uniqueness of path and remove non-unique paths
    non_unique_paths = []
    for path in unique_paths:
        if len(path) > 1:
            if non_unique_alert:
                print("ALERT: Graph has non-unique paths:", path)
            non_unique_paths.append(path)
            unique_paths.remove(path)

    # Remove outer brackets
    unique_paths = [path[0] for path in unique_paths]

    # Select paths of minimal length
    unique_paths = [path for path in unique_paths if len(path) >= min_length]

    return unique_paths, non_unique_paths


def get_SPD_matrix(adj_m):
    """Return matrix with shortest path distances between nodes.

    From adjacency matrix.
    """
    adj_m = np.array(adj_m)
    G = nx.from_numpy_array(adj_m)  # add create_using=nx.DiGraph if needed

    return get_SPD_matrix_from_G(G)


def get_SPD_matrix_from_G(G):
    """Return matrix with shortest path distances between nodes.

    From nx.Graph.
    """
    # Compute shortest path distance matrix using Floyd-Warshall numpy version
    spd_m = nx.floyd_warshall_numpy(G, weight="weight")

    return np.array(spd_m)


def get_cosd_mat(p, env_size=[900, 900]):
    """Get cosine distance matrix for a position array of shape (x, y) or (1, x, y)."""
    if isinstance(p, list):
        p_array = np.array(p, dtype=float)
        p_array -= np.array(env_size) / 2  # to center in env center
        if p_array.ndim == 2:  # (8,2)
            return cosine_distances(p_array)
        elif p_array.ndim == 3 and p_array.shape[0] == 1:  # (1, 8, 2)
            return cosine_distances(p_array[0])
    return np.nan


def dijkstra_multiple_paths(G, source):
    """Dijkstra's algorithm to compute shortest paths and detect non-unique paths."""
    dist = {node: float("inf") for node in G.nodes}
    dist[source] = 0
    predecessors = {node: [] for node in G.nodes}  # Track multiple predecessors
    pq = [(0, source)]  # Priority queue (distance, node)

    while pq:
        current_dist, u = heapq.heappop(pq)
        # If this is not the shortest distance, skip processing
        if current_dist > dist[u]:
            continue

        for v, data in G[u].items():
            weight = data["weight"]
            new_dist = current_dist + weight
            # If a new shortest path is found for node v
            if new_dist < dist[v]:
                dist[v] = new_dist
                predecessors[v] = [u]  # Reset predecessors
                heapq.heappush(pq, (new_dist, v))
            # If the same shortest distance is found (non-unique path)
            elif new_dist == dist[v]:
                predecessors[v].append(u)

    return dist, predecessors


def get_unique_sp_mat(adj_m):
    """Detect whether there are non-unique shortest paths in a graph based in adjacency matrix."""
    G = nx.from_numpy_array(adj_m)

    unique_spd_m = np.ones(np.shape(adj_m))
    for source_node in G.nodes:
        dist, predecessors = dijkstra_multiple_paths(G, source_node)
        for target_node in G.nodes:
            if len(predecessors[target_node]) > 1:
                unique_spd_m[source_node, target_node] = False
    return unique_spd_m


def get_dist_mats(pos, adj_m):
    """Calculate shortest path distance matrix (spd_m), weighted spd_m, and euclidean distance matrix (euc_m)."""
    spd_m = get_SPD_matrix(adj_m)
    eucd_m = euclid_dist_matrix(pos)
    posw_adj_m = adj_m * eucd_m
    wspd_m = get_SPD_matrix(posw_adj_m)

    return spd_m, wspd_m, eucd_m


def flatten_tril_mat(matrix):
    """Return upper triangle (without diagonal) of matrix as flattened list."""
    matrix = np.array(matrix)
    n = matrix.shape[0]  # Get the matrix size (assuming square)
    # Get upper triangle indices, excluding diagonal
    upper_tri_indices = np.triu_indices(n, k=1)

    return matrix[upper_tri_indices].tolist()  # Convert to a list

    # return squareform(matrix)

# Calculate additional graph properties {{{


def get_comm_matrix(adj_m):
    """Calculate communicability matrix from matrix exponential."""
    adj_m = adj_m / adj_m.max()  # Normalize
    return scipy.linalg.expm(adj_m)


def graph_resolvent(A, lambd):
    """
    Compute the resolvent of a graph's adjacency matrix.

    Returns:
        numpy.ndarray: Resolvent matrix R(λ, A).
    """
    # Identity matrix
    Id = np.eye(A.shape[0])

    # Resolvent computation
    try:
        R = np.linalg.inv(lambd * Id - A)
        return R
    except np.linalg.LinAlgError:
        raise ValueError(
            "Matrix is singular at the given λ (likely an eigenvalue)."
        )

# }}}
# Run MDS {{{


def run_mds(dist_m, nb_dim=2, seed=None, n_init=4, return_stress=False):
    """Run an MDS embedding for a given distance matrix."""
    contains_infs = np.isinf(dist_m).any()

    if not contains_infs:
        mds = MDS(n_components=nb_dim,
                  dissimilarity="precomputed",
                  n_init=n_init,
                  random_state=seed)
        x_mds = mds.fit_transform(dist_m)
        if return_stress:
            return mds.stress_
    else:
        # Set embedding to nan.
        x_mds = np.full((len(dist_m), nb_dim), np.nan)
        if return_stress:
            return np.nan
    

    return x_mds


# }}}


if __name__ == "__main__":
    pass
