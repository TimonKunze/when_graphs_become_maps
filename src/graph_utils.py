import numpy as np
import networkx as nx

from typing import Union, Tuple, List
from scipy.spatial.distance import squareform

import src.base_encodings as sbe

# Convert between symm. adjacency matrix and a list of its upper triangle {{{


def get_upper_triangle_without_diagonal(matrix, checks=True):
    """Return the upper triangle of a matrix without diag."""
    return squareform(matrix, force="tovector", checks=checks)


def fill_upper_triangle_no_diag(lst, checks=True):
    """Efficiently sort a list into the upper triangle of a matrix without including the diagonal."""
    full_matrix = squareform(lst, force="tomatrix", checks=checks)
    upper_triu = np.triu(full_matrix, k=1)  # with 0s on diagonal (k=1)
    return upper_triu


# }}}
# Convert between symm. adjacency matix and base16 {{{


def adjm_to_base16(adj_m):
    """Convert symmetric adjacency matrix to string in base16."""
    bin_list = get_upper_triangle_without_diagonal(adj_m)
    return sbe.binary_list_to_base16(bin_list)


def base16_to_adjm(b16_string):
    """Convert string in base16 to symmetric adjacency matrix."""
    bin_list = sbe.base16_decode_to_binary_list(b16_string)
    adj_m = fill_upper_triangle_no_diag(bin_list)
    adj_m += adj_m.T
    return adj_m


# }}}
# Graph descriptions (cycles, ...) {{{


def get_cycle_lengths(G):
    """Detect all cycles in the undirected graph G and returns their lengths.

    Parameters:
    - G (networkx.Graph): The input undirected graph.

    Returns:
    - List[int]: A list of lengths of cycles found in the graph.
    """
    # Find all cycles in the graph
    cycles = nx.cycle_basis(G)

    # Compute the lengths of each cycle
    cycle_lengths = [len(cycle) for cycle in cycles]

    return cycle_lengths


def calculate_sparsity(num_nodes, num_edges, directed=True):
    """Calculate the sparsity of a graph."""
    # Calculate the maximum possible number of edges
    if directed:  # directed graph
        max_edges = num_nodes * (num_nodes - 1)
    else:
        max_edges = num_nodes * (num_nodes - 1) // 2

    # Calculate sparsity
    sparsity = 1 - (num_edges / max_edges)
    return sparsity


def count_hubs(G, threshold=None, percentile=90):
    """
    Count hubs in the graph based on a degree threshold or percentile.

    Parameters:
    - G (networkx.Graph or networkx.DiGraph): The input graph.
    - threshold (int, optional): The degree threshold to classify a node as a hub.
    - percentile (float, optional): The percentile of the degree distribution to classify a node as a hub.

    Returns:
    - int: The number of hubs in the graph.
    """
    # Get the degree of each node
    degrees = dict(G.degree())
    # Calculate the degree values
    degree_values = list(degrees.values())
    if threshold is None:
        # Calculate degree threshold using specified percentile
        threshold = np.percentile(degree_values, percentile)
    # Count nodes that have degree greater than or equal to threshold
    num_hubs = sum(deg >= threshold for deg in degree_values)

    return num_hubs


def get_adj_matrix_from_edges(edge_set, nb_nodes):
    """Build adjacency matrix from edge set for an undirected graph."""
    # Initialize
    adj_m = np.zeros((nb_nodes, nb_nodes), dtype=int)
    # Iterate over edge set
    for edge in edge_set:
        i, j = edge
        adj_m[i][j] = 1
        adj_m[j][i] = 1  # Symmetricity

    return adj_m


def communicability_weight_matrix(
    adj_or_g: Union[np.ndarray, nx.Graph],
    use_edge_weights: bool = True,
) -> np.ndarray:
    """Compute the communicability matrix W where W[i,j] = (e^A)_{ij}."""
    # Build working graph with desired weight semantics
    if isinstance(adj_or_g, np.ndarray):
        A = np.asarray(adj_or_g, dtype=float)
        if use_edge_weights:
            G = nx.from_numpy_array(A)  # numeric entries become "weight"
        else:
            G = nx.from_numpy_array((A != 0).astype(float))  # unweighted (1 where A>0)
        nodes = list(range(A.shape[0]))
    elif isinstance(adj_or_g, nx.Graph):
        G = adj_or_g.copy()
        nodes = sorted(G.nodes())
        if not use_edge_weights:
            nx.set_edge_attributes(G, {e: 1.0 for e in G.edges()}, name="weight")
    else:
        raise TypeError("adj_or_g must be a NumPy array or a NetworkX Graph.")

    # Compute communicability (dict-of-dicts), then pack into array W
    C = nx.communicability(G)
    idx = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)
    W = np.zeros((n, n), dtype=float)
    for u in nodes:
        for v, val in C[u].items():
            W[idx[u], idx[v]] = float(val)
    return W


def hub_normalized_weight_matrix(
        adj_or_g: Union[np.ndarray, nx.Graph],
) -> Union[np.ndarray, Tuple[np.ndarray, List]]:
    """Symmetric normalized adjacency (hub-normalized).

        W_sym = D^{-1/2} A D^{-1/2},  with  W_ij = A_ij / sqrt(d_i d_j)

    Parameters
    ----------
    adj_or_g : np.ndarray or nx.Graph
        - If np.ndarray: an (n x n) adjacency matrix.
        - If nx.Graph: the graph (weights ignored; uses unweighted degrees).

    Returns
    -------
    W_sym : np.ndarray
        Hub-normalized weight matrix (n x n).
    """
    if isinstance(adj_or_g, np.ndarray):
        A = np.asarray(adj_or_g, dtype=float)
        nodes = list(range(A.shape[0]))
    elif isinstance(adj_or_g, nx.Graph):
        nodes = sorted(adj_or_g.nodes())
        A = nx.to_numpy_array(adj_or_g, nodelist=nodes, dtype=float)
    else:
        raise TypeError("adj_or_g must be a NumPy array or a NetworkX Graph.")

    # Degree vector (row sums). Handle isolated nodes safely.
    deg = A.sum(axis=1)
    with np.errstate(divide="ignore"):
        d_half_inv = 1.0 / np.sqrt(deg)
    d_half_inv[~np.isfinite(d_half_inv)] = 0.0  # set inf/NaN to 0 for isolated nodes
    D_half_inv = np.diag(d_half_inv)

    W_sym = D_half_inv @ A @ D_half_inv

    return W_sym


def rotate_point(point, angle, origin=(0, 0)):
    """Rotate a point counterclockwise by a given angle around a specified origin.

    Parameters:
    - point (tuple): The (x, y) coordinates of the point to rotate.
    - angle (float): The rotation angle in degrees.
    - origin (tuple): The (x, y) coordinates of the rotation origin.

    Returns:
    - numpy.ndarray: The new (x, y) coordinates after rotation.
    """
    # Convert angle from degrees to radians
    theta = np.radians(angle)
    # Define rotation matrix
    rotation_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    # Translate point to origin
    translated_point = np.array(point) - np.array(origin)
    # Perform rotation
    rotated_point = np.dot(rotation_matrix, translated_point)
    # Translate point back
    rotated_point += np.array(origin)

    return rotated_point


def rotate_points(points, angle, origin=(0, 0)):
    """Rotate all points in a list."""
    new_pts = np.zeros_like(points)
    for i, point in enumerate(points):
        new_pts[i] = rotate_point(point, angle, origin)
    return new_pts

# }}}


if __name__ == "__main__":
    adj_m = np.array(
        [
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [0, 0, 0, 0],
        ]
    )
    adj_m += adj_m.T
    x = adjm_to_base16(adj_m)
    print(x)
    print(type(x))

    y = base16_to_adjm(x)
    print(y)
