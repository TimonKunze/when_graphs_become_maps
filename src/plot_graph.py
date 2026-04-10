import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

import matplotlib.patches as patches

from matplotlib.colors import to_rgb

import src.opt_position_utils as sop
import src.graph_utils as sgu


def axplot_graph(
    adj_mat,
    pos="spring",
    edge_labels=False,
    alpha=None,
    env_size=None,
    circ_rad=None,
    grid_spacing=None,
    # edge_mat=None,
    node_color="skyblue",
    ax=None,
    **args,
):
    """Ax object of graph based on adjacency matrix.

    Parameters:
        - adj_mat (numpy.ndarray): The adjacency matrix representing
            the graph structure.
        - pos (string or array, optional): Node positions. Default is
            spring, resulting in a spring layout.
        - edge_labels (bool, optional): Whether to display edge labels.
            Default is False.
        - alpha (float, optional): Transparency of graph elements.
            Default is None.
        - env_size (bool or array-like, optional): Environment size.
        Default is True, auto-determined from adjacency matrix.
        - circ_rad (float, optional): Radius of a circle at environment
            center. Default is None.
        - ax (matplotlib.axes.Axes, optional): Axes object. Default is
            None, using current axes.

    Returns:
        - None
    """
    graph = nx.from_numpy_array(np.array(adj_mat), create_using=nx.DiGraph())

    if ax is None:
        ax = plt.gca()

    # Add environemnt
    if env_size is not None:
        env_size = np.array(env_size)

        rectangle = patches.Rectangle(
            (0, 0),
            env_size[0],
            env_size[1],
            linewidth=1,
            edgecolor=None,
            facecolor=to_rgb("#acd871"),
        )
        ax.add_patch(rectangle)

    # Add circle
    if circ_rad is not None:
        center = tuple(env_size / 2)
        circle = patches.Circle(center, circ_rad, edgecolor="grey",
                                facecolor="none")
        ax.add_patch(circle)

    # Add grid
    if grid_spacing is not None:
        points = sop.grid_points_in_circle(grid_spacing)
        for point in points:
            circle = patches.Circle(point, 1, edgecolor="black",
                                    facecolor="none")
            ax.add_patch(circle)

    edge_colors = "k"

    # Use layout algorithm of choice no position specified
    # (default is spring layout)
    if (isinstance(pos, str) and pos == "spring"):
        pos = nx.spring_layout(graph, **args)
    if (isinstance(pos, str) and pos == "circ"):
        pos = nx.circular_layout(graph)

    # Draw graph
    nx.draw(
        graph,
        pos,
        with_labels=True,
        node_color=node_color,
        node_size=200,
        edge_color=edge_colors,
        linewidths=1,
        font_size=8,
        arrows=False,
        alpha=alpha,
        ax=ax,
    )

    # Add edge labels (weights)
    if edge_labels:
        edge_labels = nx.get_edge_attributes(graph, "weight")
        edge_labels = {k: round(v, 1) for k, v in edge_labels.items()}
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels=edge_labels, font_size=7, ax=ax
        )

    # Set aspect ratio
    ax.set_aspect("equal")  # , adjustable='box')


def plot_env_grid(grid_spacing, env_size=[900, 900]):
    """Plot environment grid."""
    circ_rad = env_size[0] / 2 - 40
    center = (env_size[0] / 2, env_size[1] / 2)
    points = sop.grid_points_in_circle(grid_spacing, center, circ_rad)

    # Adjmat not really necessary only for axplot_graph function
    adj_mat = np.array(
        [
            [0, 1, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    adj_mat = adj_mat + adj_mat.T

    fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(4, 4))
    axplot_graph(adj_mat, None, env_size=env_size, circ_rad=circ_rad, ax=axs)
    for point in points:
        circle = patches.Circle(point, 1, edgecolor="black", facecolor="none")
        axs.add_patch(circle)
    axs.set_title("")
    fig.tight_layout()
    plt.show()


def rotate_points(center, points, angle_rad):
    """Wrap rotate_points function of graph utils."""
    angle_degr = np.degrees(angle_rad)
    return sgu.rotate_points(points, angle_degr, center)


if __name__ == "__main__":
    pass
