import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Plot p values {{{


def annot_stat(annotation, x1, x2, y, h=None, col="k", 
               fontsize=10,
               ax=None):
    """Annotates plot with a significance marker (e.g., '*')
    and a connecting line.

    Parameters:
        annotation : str
            The significance annotation (e.g., '*', '**').
        x1, x2 : float
            X-coordinates for the start and end of the line.
        y : float
            Baseline y-coordinate for the line.
        h : float
            Height of the vertical lines.
        col : str, optional
            Line and text color (default is 'k').
        ax : matplotlib.axes.Axes, optional
            Axes to annotate (default is current axes).

    Returns: None
    """
    if h is None:
        h = y * 0.035
    ax = plt.gca() if ax is None else ax
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.5, c=col)
    ax.text((x1 + x2) * 0.5, y + h, annotation, 
            ha="center", va="bottom", color=col,
            fontsize=fontsize)


def annot_stat_bar(star, x, y, col="k", rotation=0, ax=None):
    """Annotates a statistical significance result (e.g., p-value or
    stars) on a plot, typically used to label
    bar plots or boxplots with statistical information.
    """
    ax = plt.gca() if ax is None else ax
    ax.text(x, y, star, ha="center", va="center", color=col, rotation=rotation)


def calc_stars(p_val, near_to=False):
    """Standards for one to fours asterisks"""
    if p_val < 0.0001:
        # stars = r"$*\!*\!*\!*$"
        stars = "****"
    elif p_val < 0.001:
        # stars = r"$*\!*\!*$"
        stars = "***"
    elif p_val < 0.01:
        # stars = r"$*\!*$"
        stars = "**"
    elif p_val <= 0.05:
        stars = r"$*$"
    elif near_to and p_val <= 0.1:
        stars = r"$^{+}$"
    elif np.isnan(p_val):
        stars = ""
    else:
        stars = r"$^{\text{ns}}$"
    return stars


# }}}
# Enuemrate Plots {{{


def enumerate_plot(letter, ax=None):
    """Adds a bold letter annotation to the top-left corner of a plot."""
    if ax is None:
        ax = plt.gca()
    ax.text(0.03, 0.95, letter, fontweight="bold", transform=ax.transAxes)


# }}}
# Draw Stripplot lines {{{


def get_indices_of_pathcollections(ax):
    """Retrieve indices of PathCollection objects from
    a Matplotlib Axes object.

    This function scans the children of the given Matplotlib
    Axes object and returns the indices of those children that
    are instances of `matplotlib.collections.PathCollection`.
    This is useful for identifying scatter plot elements or
    similar collections within the Axes.
    """
    import matplotlib.collections as mcollections

    idxs = []
    for i, elm in enumerate(ax.get_children()):
        if isinstance(elm, mcollections.PathCollection):
            idxs.append(i)
    return idxs


def draw_stripplot_lines(set1, set2, ax):
    """Draw connecting lines between points in a Seaborn strip plot.

    This function connects data points from two sets in a strip plot
    by drawing lines between corresponding points. It assumes that
    `set1` and `set2` represent the data points from two different
    conditions or categories in a strip plot and that these points
    are plotted on the same axis.

    Solution based on: https://stackoverflow.com/questions/51155396/plotting-colored-lines-connecting-individual-data-points-of-two-swarmplots
    """
    # draw connecting lines between points in seaborn strip plot
    idxs = get_indices_of_pathcollections(ax)
    idxs = idxs[:2]
    assert len(idxs) <= 2, f"Error: List length is {len(idxs)}, which is longer than 2."
    idx0, idx1 = idxs

    # get the locations of points
    locs1 = ax.get_children()[idx0].get_offsets()
    locs2 = ax.get_children()[idx1].get_offsets()
    assert locs1.shape == locs2.shape, "Data not in same shape."

    # WARNING: it seems to be correct without sorting, but better be
    # carefull and check a few times.
    # # before plotting, we need to sort so that the data points
    # # correspond to each other as they did in "set1" and "set2"
    # sort_idxs1 = np.argsort(set1)
    # sort_idxs2 = np.argsort(set2)
    #
    # # revert "ascending sort" through sort_idxs2.argsort(),
    # # and then sort into order corresponding with set1
    # locs2_sorted = locs2[sort_idxs2.argsort()][sort_idxs1]
    locs2_sorted = locs2  # Remove when actually sorted

    for i in range(locs1.shape[0]):
        x = [locs1[i, 0], locs2_sorted[i, 0]]
        y = [locs1[i, 1], locs2_sorted[i, 1]]
        ax.plot(x, y, color="black", alpha=0.1)


# }}}


def create_gridspec_fig(
        layout: list, figsize=(8, 6), spacing=(0.3, 0.3), panel_labels=True):
    """Create a figure with a flexible GridSpec layout.

    Parameters:
    - layout: List of tuples defining subplot positions
        (row_start, row_end, col_start, col_end).
    - figsize: Tuple, figure size (width, height).
    - spacing: Tuple, (hspace, wspace) for subplot spacing.
    - panel_labels: Bool, whether to label subplots (a, b, c...).

    Returns:
    - fig: Matplotlib figure object.
    - axs: List of subplot axes.
    """
    num_rows = max(pos[1] for pos in layout)  # Max row index
    num_cols = max(pos[3] for pos in layout)  # Max col index

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(num_rows, num_cols, figure=fig)

    axs = []
    for i, (r1, r2, c1, c2) in enumerate(layout):
        ax = fig.add_subplot(gs[r1:r2, c1:c2])
        axs.append(ax)

        if panel_labels:
            ax.text(-0.1, 1.1, chr(97 + i), transform=ax.transAxes, fontsize=12,
                    fontweight="bold", va="top")

    fig.subplots_adjust(hspace=spacing[0], wspace=spacing[1])

    return fig, axs


if __name__ == "__main__":
    zero = pd.DataFrame(
        {
            "Number of Research Years": [0, 1, 2],
            "Total Publications": 100 * np.random.random(size=3),
            "Publications During Residency": 100 * np.random.random(size=3),
            "Publications Before & After Residency": 100 * np.random.random(size=3),
            "H Index": 10 * np.random.random(size=3),
        }
    )

    fig, axes = plt.subplots(2, 2, sharex=False, sharey=True, figsize=(8, 8))

    ax1 = sns.barplot(
        ax=axes[0, 0], x=zero["Number of Research Years"], y=zero["Total Publications"]
    )
    ax2 = sns.barplot(
        ax=axes[0, 1],
        x=zero["Number of Research Years"],
        y=zero["Publications During Residency"],
    )
    ax3 = sns.barplot(
        ax=axes[1, 0],
        x=zero["Number of Research Years"],
        y=zero["Publications Before & After Residency"],
    )
    ax4 = sns.barplot(
        ax=axes[1, 1], x=zero["Number of Research Years"], y=zero["H Index"]
    )

    ax1.text(0.05, 0.95, "A", fontweight="bold", transform=ax1.transAxes)
    ax2.text(0.05, 0.95, "B", fontweight="bold", transform=ax2.transAxes)
    ax3.text(0.05, 0.95, "C", fontweight="bold", transform=ax3.transAxes)
    ax4.text(0.05, 0.95, "D", fontweight="bold", transform=ax4.transAxes)

    annot_stat("*", 1, 2, 100, 5, ax=ax1)
    annot_stat("***", 0, 2, 120, 5, ax=ax1)

    annot_stat("*", 1, 2, 100, 5, ax=ax2)
    annot_stat("***", 0, 2, 120, 5, ax=ax2)

    annot_stat("*", 1, 2, 100, 5, ax=ax3)
    annot_stat("***", 0, 2, 120, 5, ax=ax3)

    annot_stat("***", 1, 2, 10, 5, ax=ax4)
    annot_stat("*", 0, 2, 20, 5, ax=ax4)

    sns.despine()
    plt.show()

    # Sample data
    x = np.linspace(0, 10, 100)
    y1, y2, y3, y4 = np.sin(x), np.cos(x), np.exp(-x), np.log1p(x)

    # Define layout [(row_start, row_end, col_start, col_end)]
    layout = [
        (0, 1, 0, 2),  # Large plot (top row, spans two columns)
        (1, 2, 0, 1),  # Bottom-left
        (1, 2, 1, 2),  # Bottom-right
    ]

    # Create figure with the helper function
    fig, axs = create_gridspec_fig(layout, figsize=(8, 6))

    # Plot data
    axs[0].plot(x, y1, label="sin(x)")
    axs[1].plot(x, y2, label="cos(x)", color="red")
    axs[2].plot(x, y3, label="exp(-x)", color="green")

    # Add legends
    for ax in axs:
        ax.legend()
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")

    plt.show()
