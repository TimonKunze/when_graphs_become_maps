import numpy as np
import scipy.special

from shapely.geometry import LineString

import src.distance_utils as sdu
import src.graph_utils as sgu

# Sort paths by Euclidean pair difference {{{

def pair_diff(pair, euc_mat, spd_mat):
    """Calculate difference between pairs based on euclidean (EUCL) distance
    by subtracting always from the path that has larger SPD and 
    subtracting with the one that has smaller SPD shortest path distance 
    (SPD) matrix.
    
    Return:
       Sign of difference tells whether it is congruent or incongruent.
       High negative values show strong incongruence.
       High positive values show strong congruence.
    """
    [path_1, path_2] = pair
    # Get distances
    spd_p1 = spd_mat[path_1[0]][path_1[-1]]
    spd_p2 = spd_mat[path_2[0]][path_2[-1]]
    eu_p1 = euc_mat[path_1[0]][path_1[-1]]
    eu_p2 = euc_mat[path_2[0]][path_2[-1]]
    # Calculate difference
    if spd_p1 > spd_p2:
        diff = eu_p1 - eu_p2
    elif spd_p1 < spd_p2:
        diff = eu_p2 - eu_p1
    else:
        diff = 0
        print("Alert: Equal SPD!")
    return diff


def bubble_sort_pair_diff(arr, dist_mat, spd_mat):
    """Sort array in ascending order based on the difference
    defined in a distance matrix, i.e. smallest differences first,
    largest last.

    Returns:
        sorted array
    """
    n = len(arr)
    if n == 0:
        return arr
    else:
        for i in range(n-1):
            swapped = False
            for j in range(0, n-i-1):
                if pair_diff(arr[j], dist_mat, spd_mat) > pair_diff(arr[j+1], dist_mat, spd_mat):
                    swapped = True
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
            if not swapped:
                return arr

# }}}
# Get congruent and incongruent pairs {{{

def arrays_equal(arr1, arr2):
    """Check if array are equal"""
    return arr1 == arr2

def exclude_self_similar_cases(nested_list):
    """ Exclude Self-similar lists in a list of lists. 
    Self-similar lists are lists, that are the if reversed.
    """
    new_list = []

    for item in nested_list:
        is_self_similar = False

        for existing_item in new_list:
            if (arrays_equal([item[0], item[1]], existing_item) or
                arrays_equal([item[0][::-1], item[1]], existing_item) or
                arrays_equal([item[0], item[1][::-1]], existing_item) or
                arrays_equal([item[0][::-1], item[1][::-1]], existing_item) or
                arrays_equal([item[1], item[0]], existing_item) or
                arrays_equal([item[1][::-1], item[0]], existing_item) or
                arrays_equal([item[1], item[0][::-1]], existing_item) or
                arrays_equal([item[1][::-1], item[0][::-1]], existing_item)):
                is_self_similar = True
                break

        if not is_self_similar:
            new_list.append(item)

    return new_list


def get_congr_and_incongr_pairs(ADJ_m, SPD_m, EUCL_m, 
                                min_len_paths=3, 
                                nb_similar_pairs=1,
                                nb_pairs=None,
                                verbose=False,
                                max_len_paths=None,
                               ):
    """
    Calculate congruent and incongruent pairs based on the shortest path distances
    (SPD) on the graph and the Euclidean distance between the start and end nodes.
    Also calculates the congr. and incongr. pairs based SPD and w-SPD if 
    a weighted shortest path distance matrix is inserted instead of an Euclidean
    distance matrix.

    This function identifies pairs of paths in the graph that are congruent 
    (i.e., both SPD and Euclidean distance are either 
    both larger or both smaller) or incongruent (i.e., one distance is 
    larger and the other is smaller). The function returns these pairs 
    and optionally prints detailed information.

    Parameters:
    -----------
    ADJ_m : numpy.ndarray
        Adjacency matrix representing the graph.
    SPD_m : numpy.ndarray
        Shortest path distance matrix.
    EUCL_m : numpy.ndarray
        Euclidean distance matrix (or weighted shortest distance matrix).
    min_len_paths : int, optional (default=3)
        Minimum length of paths to consider for pairing.
    nb_similar_pairs : int, optional (default=1)
        Number of similar pairs to consider. Currently not used in the function.
    nb_pairs : int or None, optional (default=None)
        Number of pairs to include in the output. If None, all pairs are included.
    verbose : bool, optional (default=False)
        If True, prints detailed information about the pairs and their differences.

    Returns:
    --------
    congruent_pairs : list of list of tuple
        List of congruent pairs, where each pair is a list of two paths.
    incongruent_pairs : list of list of tuple
        List of incongruent pairs, where each pair is a list of two paths.

    Notes:
    ------
    The function first obtains unique and non-unique paths of at least `min_len_paths` 
    length from the adjacency matrix. It then iterates through these paths to 
    determine congruent and incongruent pairs based on their shortest path 
    distances and Euclidean distances. The pairs are sorted and filtered to 
    exclude self-similar cases, and the top `nb_pairs` pairs are selected.
    """
    
    # Get unique (and non-unique) paths
    unique_paths, non_unique_paths = sdu.get_unique_paths_of_minL(ADJ_m, min_len_paths)

    # Take only unique paths <= max_len_path
    if max_len_paths is not None:
        unique_paths_maxlen = []
        for path in unique_paths:
            if len(path) <= max_len_paths:
                unique_paths_maxlen.append(path)
        unique_paths = unique_paths_maxlen

    # Get congruent and incongruent pairs
    congruent_pairs = []
    incongruent_pairs = []
    same_length_pairs = []
    other_pairs = []
    for path_1 in unique_paths:
        for path_2 in unique_paths:
            # Get SPD distance lengths
            SPD_P1 = SPD_m[path_1[0]][path_1[-1]]
            SPD_P2 = SPD_m[path_2[0]][path_2[-1]]
            # Get euclidean distance length
            EUCL_P1 = EUCL_m[path_1[0]][path_1[-1]]
            EUCL_P2 = EUCL_m[path_2[0]][path_2[-1]]
            # Get congruent, incongruent, and same-distance pairs
            if (SPD_P1 < SPD_P2 and EUCL_P1 < EUCL_P2) or (SPD_P1 > SPD_P2 and EUCL_P1 > EUCL_P2):
                congruent_pairs.append([path_1, path_2])
            elif (SPD_P1 > SPD_P2 and EUCL_P1 < EUCL_P2) or (SPD_P1 < SPD_P2 and EUCL_P1 > EUCL_P2):
                incongruent_pairs.append([path_1, path_2])
            elif SPD_P1 == SPD_P2 or EUCL_P1 == EUCL_P2:
                same_length_pairs.append([path_1, path_2]) 
            else:
                other_pairs.append([path_1, path_2]) # should be empty

    # Sort congruent pairs by largest difference in Euclidean distance
    congruent_pairs = bubble_sort_pair_diff(congruent_pairs, EUCL_m, SPD_m)
    congruent_pairs.reverse()
    # Sort incongruent pairs by smallest difference in Euclidean distance
    incongruent_pairs = bubble_sort_pair_diff(incongruent_pairs, EUCL_m, SPD_m)
    # Note that we only take the Euclidean difference into account:
    # - We expect a stronger effect if the Euclidean distance beween
    #   congruent pairs is larger, and we also expect a stronger effect
    #   if the difference between incongruent pairs is smaller.
    # For the current graph there are only STP differences of 1, anyways.
    # But this might change for bigger graphs.

    congruent_pairs = exclude_self_similar_cases(congruent_pairs)
    incongruent_pairs = exclude_self_similar_cases(incongruent_pairs)
    
    # Select how many pairs ("nb_pairs") to be included (for all pairs nb_pairs=None)
    # Set to number that is lower or equal the numbers of max nb of pairs in one of the two.
    congruent_pairs = congruent_pairs[:nb_pairs]
    incongruent_pairs = incongruent_pairs[:nb_pairs]
    if len(congruent_pairs) != len(incongruent_pairs) and verbose==True:
        print(f"""Alert: Congruent pairs (N={len(congruent_pairs)}) and  incongruent pairs (N={len(incongruent_pairs)}) 
                  are  not of equal number! Choose a smaller number of pairs.""")
    
    # Get the exact difference between the first and last pair for control
    if congruent_pairs == []:
        congr_pair_diff = None
    else:
        congr_pair_diff = [pair_diff(congruent_pairs[0], EUCL_m, SPD_m), 
                           pair_diff(congruent_pairs[-1], EUCL_m, SPD_m)]
    if incongruent_pairs == []:
        incongr_pair_diff = None
    else:
        incongr_pair_diff = [pair_diff(incongruent_pairs[0], EUCL_m, SPD_m), 
                             pair_diff(incongruent_pairs[-1], EUCL_m, SPD_m)]
        
    # Print results
    if verbose is True:
        print(f"Congruent-trial pairs: Nb={len(congruent_pairs)}, Pair-diff (1st&last)={congr_pair_diff}")
        print("Pairs=", congruent_pairs)
        print("")
        print(f"Incongruent-trial pairs: Nb={len(incongruent_pairs)}, Pair-diff (1st&last)={incongr_pair_diff}")
        print("Pairs=", incongruent_pairs)
        print("")
        print("FURHTER INFO:")
        print(f"Same-length pairs: Nb={len(same_length_pairs)}") #, Paths=", same_length_pairs)
        #print(f"Other pairs: Nb={len(other_pairs)}, Pairs=", other_pairs)
        print(f"Congr. and Incongr. pairs are sampled from unique paths longer or equal to {min_len_paths}: Nb={len(unique_paths)}")
        #print("Pairs=", unique_paths)
        print("")
        print("")

    return congruent_pairs, incongruent_pairs#, congr_pair_diff, incongr_pair_diff


# }}}
## Optimize Graph Positioning (Only python)
# Get grid environemnt {{{

def grid_points_in_circle(grid_spacing, center=None, radius=None, 
                          env_size=[900,900]):
    """
    Returns a list of grid points within a circle.

    Parameters:
    - center: Tuple (x, y) representing the center of the circle.
    - radius: Radius of the circle.
    - grid_spacing: Spacing between grid points.

    Returns:
    - List of grid points within the circle.
    """
    if center is None and radius is None:
        radius = env_size[0]/2 - 40
        center = (env_size[0]/2, env_size[1]/2)

    points = []
    center_x, center_y = center

    # Calculate the range of grid points to check based on circle radius
    min_x = int((center_x - radius) // grid_spacing)
    max_x = int((center_x + radius) // grid_spacing) + 1
    min_y = int((center_y - radius) // grid_spacing)
    max_y = int((center_y + radius) // grid_spacing) + 1

    for x in range(min_x, max_x):
        for y in range(min_y, max_y):
            # Calculate distance between grid point and circle center
            distance = np.sqrt((x * grid_spacing - center_x)**2 + (y * grid_spacing - center_y)**2)
            # Check if the point is within the circle
            if distance <= radius:
                points.append((x*grid_spacing, y*grid_spacing))

    return points

# }}}
# Find Similar Positions {{{

def translate_2d_pt(point, x, y):
    """Translate a point in 2D by x and y."""
    return point[0]+x, point[1]+y


def translate_2d_pts(points, x, y):
    """Translate a set of points in 2D by x and y."""
    new_pts = np.zeros_like(points)
    for i, point in enumerate(points):
        new_pts[i] = translate_2d_pt(point, x, y)
    return new_pts


def arr_in(nested_arr, arr_to_compared):
    """Test whether arr_to_compared is contained in the nested 
    array.
    """
    for arr in nested_arr:
        if np.array_equal(arr, arr_to_compared):
            return True
    return False
    

def similar_position_found(saved_poss, curr_pos, env_size, grid_spacing):
    """
    Check for similar graph positionings in a saved list.

    This function determines if a given graph positioning (curr_pos) is similar 
    to any of the previously saved positionings (saved_poss). Two positionings 
    are considered similar if they can be transformed into one another through 
    translation, 90-degree rotation, 180-degree rotation, or 270-degree rotation, 
    or a combination of these transformations. The function stops and returns 
    True as soon as it finds a similar positioning. If no similar positioning is 
    found after checking all transformations, it returns False.

    Parameters:
    -----------
    saved_poss : list of lists of tuples
        A list of previously saved graph positionings, each positioning being a 
        list of coordinates (tuples).
    curr_pos : list of tuples
        The current graph positioning to be checked for similarity.
    env_size : tuple
        The size of the environment (width, height) within which translations 
        are considered.
    grid_spacing : int or float
        The spacing interval at which translations are applied.

    Returns:
    --------
    bool
        True if a similar positioning is found in saved_poss, False otherwise.

    Notes:
    ------
    - The function considers translations by multiples of grid_spacing within 
      the range defined by env_size.
    - The function first checks the current position and its 90-degree, 
      180-degree, and 270-degree rotations, then applies translations to these 
      positions and checks for similarity with saved_poss.
    - The function handles the special case where curr_pos consists entirely 
      of (0,0) coordinates by returning False immediately.
    """
    if curr_pos == [(0, 0)] * len(curr_pos):
        return False
    curr_pos_90 = sgu.rotate_points(curr_pos, 90, np.array(env_size)/2)
    curr_pos_180 = sgu.rotate_points(curr_pos, 180, np.array(env_size)/2)
    curr_pos_270 = sgu.rotate_points(curr_pos, 270, np.array(env_size)/2)

    for i in range(0, env_size[0], grid_spacing):
        for j in range(0, env_size[1], grid_spacing):
            translations = [(i, j), (-i, j), (i, -j), (-i, -j)]
            for dx, dy in translations:
                curr_pos = translate_2d_pts(curr_pos, dx, dy)     
                curr_pos_90 = translate_2d_pts(curr_pos_90, dx, dy)
                curr_pos_180 = translate_2d_pts(curr_pos_180, dx, dy)
                curr_pos_270 = translate_2d_pts(curr_pos_270, dx, dy)
                if arr_in(saved_poss, curr_pos) \
                    or arr_in(saved_poss, curr_pos_90) \
                    or arr_in(saved_poss, curr_pos_180) \
                    or arr_in(saved_poss, curr_pos_270):
                    return True
    return False

# }}}
# Check Graph Planarity {{{


def check_line_cross(line1, line2):
    """
    Check if two line segments cross each other. Crossing means that 
    they share a point but do not overlap completely (i.e., they 
    intersect but are not collinear and do not share
    the same start and end points).

    Args:
        line1 (LineString): First line segment to check.
        line2 (LineString): Second line segment to check.

    Returns:
        bool: True if `line1` crosses `line2`, False otherwise.
    """
    return line1.crosses(line2)


def check_line_touch(line1, line2):
    """
    Determine whether two lines touch each other. Touching
    means that two lines intersect but do not cross
    each other at a point which is not a boundary point.

    Args:
        line1 (LineString): First line segment to check.
        line2 (LineString): Second line segment to check.

    Returns:
        bool: True if the two lines touch each other at a point
              which is not a boundary point. False otherwise.
    """
    intersection = line1.intersection(line2)
    cross = line1.crosses(line2)
    # Check whether it intersects but not crosses
    if intersection and not cross:
        start_p_l1, end_p_l1 = line1.boundary.geoms
        start_p_l2, end_p_l2 = line2.boundary.geoms
        # Check wether the lines share a start or end point 
        # (by set intersection). If yes it's not a touch.
        if {start_p_l1, end_p_l1} & {start_p_l2, end_p_l2}: 
            return False
        return True
    return False


def check_graphpos_planarity(G, pos):
    """
    Checks whether any pair of edges in the graph touch or cross 
    based on their respective positions in 2D space.

    Parameters:
    G (networkx.Graph): The input graph.
    pos (dict or list): A dictionary mapping nodes to their positions in 2D space, 
                        or a list of node positions. If a list is provided, it is 
                        converted to a dictionary where node indices start from 1.

    Returns:
    tuple: A tuple containing two boolean values indicating whether any pair of edges 
           touches or crosses in the graph.
           - First element: True if any pair of edges touches (but does not cross), 
             otherwise False.
           - Second element: True if any pair of edges crosses, otherwise False.
    """
    if isinstance(pos, list):
        pos = {index: value for index, value in enumerate(pos)}

    touches = False
    crosses = False

    edges = list(G.edges())
    lines = {(u, v): LineString([pos[u], pos[v]]) for u, v in edges}

    for i, edge1 in enumerate(edges):
        for j in range(i + 1, len(edges)):
            edge2 = edges[j]
            line1 = lines[edge1]
            line2 = lines[edge2]

            # Check whether lines touch or cross
            if not crosses and check_line_cross(line1, line2):
                crosses = True
            if not touches and check_line_touch(line1, line2):
                touches = True

            # Break and return if both are true
            if touches and crosses:
                return True, True

    return touches, crosses




# }}}
# Binomialcoeefficient and combinatory ETA {{{

def binomial_coeff(n, k):
    """Calculate binomial coefficient: n choose k. Return N."""
    return scipy.special.comb(n, k, exact=True)


def print_combinatory_ETA(n, k, it_per_s=None):
    """Print run time estimation of run over binomial coefficient
    for different iterations per second."""
    
    # Binomialcoeefficient: n choose k
    N = binomial_coeff(n, k)
    print("Binomialcoeff: ", n, " choose ", k, " = ", format(N, ","))
    print("")
    if it_per_s is not None:
        for itps in it_per_s:
            print(f"ETA {itps} it/s: {N/itps/60:.1f} min (or {N/itps/60/60:.1f} h)")
            print("")

    
# }}}

if __name__ == '__main__':
    pass
