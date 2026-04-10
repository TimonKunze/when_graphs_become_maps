import numpy as np
import pandas as pd
import seaborn as sns
import pingouin as pg
import matplotlib.pyplot as plt

from src.config import palette, dist_palette
from sklearn.cluster import KMeans

import src.distance_utils as sdu
import src.annot_plot as sap
import src.stat_test_utils as stu
import src.plot_graph as spg
from src.config import dark_orange_palette, dark_brown_palette


# General {{{

def capitalize(s: str, word=1) -> str:
    """
    Capitalize the second word in a string.
    If there is no second word, returns the string unchanged.
    """
    if word == 1:
        return s.title()
    elif word == 2:
        parts = s.split()
        if len(parts) < 2:
            return s  # nothing to do

        # Capitalize just the second word (first letter upper, rest unchanged)
        second = parts[1]
        parts[1] = second[:1].upper() + second[1:]

        return " ".join(parts)


def format_label(name: str, extended: bool = True, latex: bool = False) -> str:
    """
    Format a single predictor label into a consistent human-readable (or LaTeX) format.

    Parameters
    ----------
    name : str
        Raw predictor name (e.g., "avg_subj_spd_pp_diff")
    extended : bool
        Apply extended formatting (titles, Eucl., path dist., etc.)
    latex : bool
        If True, use LaTeX $\Delta$ instead of Unicode Δ.
    """
    diffs = False
    base = name

    # ----- Strip suffixes -----
    if base.endswith("_m_flat"):
        base = base[:-7]
    elif base.endswith("_m"):
        base = base[:-2]
    elif base.endswith("_pp_diff"):
        diffs = True
        # Handle Δ or $\Delta$
        delta = r"$\Delta$ " if latex else "Δ "
        base = delta + base[:-8]

    # ----- Build label -----
    if extended:
        if diffs:
            label = base.replace("_", " ").title()
            label = label.replace("Subj", "subj.")
            label = label.replace("Spd", "path")
            label = label.replace("Eucd", "Eucl.")
            label = label.replace("Wspd", "wtd. path")
            label = label[0].upper() + label[1:]
            label = capitalize(label, 2) 
        else:
            label = base.replace("_", " ").title()
            label = label.replace("Subj", "subj.")
            label = label.replace("Spd", "path dist.")
            label = label.replace("Eucd", "Eucl. dist.")
            label = label.replace("Wspd", "wtd. path")
            label = label.replace("Cluster1", "Cluster1 dist.")
            label = label.replace("Cluster2", "Cluster2 dist.")
            label = label.replace("Cluster3", "Cluster3 dist.")
            label = label[0].upper() + label[1:]
            label = capitalize(label, 1)

        # Special case
        if label == "Color":
            label = "Color dist."

    else:
        # compact/no extended formatting
        label = base.replace("_", " ").title()
        label = label.replace(" ", "")
        label = label.replace("Spd", "SPD")
        label = label.replace("Eucd", "EUCD")
        label = label.replace("Wspd", "WSPD")

    # ----- Post-hoc corrections -----
    if label == "Δ Subj. Eucl. Subt" or label == r"$\Delta$ Subj. Eucl. Subt":
        label = "Δ Subj. Eucl.'" if not latex else r"$\Delta$ Subj. Eucl.'"

    if label in ["Δ Avg Rand Eucl.", r"$\Delta$ Avg Rand Eucl."]:
        label = "Δ Avg. Eucl." if not latex else r"$\Delta$ Avg. Eucl."

    if label == "Avg Rand Eucl.":
        label = "Avg. Eucl."

    return label


def format_labels(names, extended=True):
    """Apply format_label to a list/sequence of names."""
    return [format_label(n, extended=extended) for n in names]

# }}}
# Plot Learning Analyses {{{

def axplot_task2_paired(dt, key, ax=None, hline=None):
    if ax is None:
        ax = plt.gca()
    
    blocks_short = ["1", "2", "3", "4", "5"]
    blocks = ["first", "second", "third", "fourth", "fifth"]

    grouped_dt = (
        dt.groupby(["subject_id", "type", "var_type"])[key].mean().reset_index()
    )

    # Plot
    sns.pointplot(
        grouped_dt, y=key, x="type", 
        hue="var_type",
        order=blocks, ax=ax,
        hue_order=grouped_dt["var_type"].unique()[::-1],
        palette=["#9C6C6C", "#3A2A29"],  
        legend=True,
    )
    sns.stripplot(
        grouped_dt,
        x="type",
        y=key,
        jitter=True,
        hue="var_type",
        dodge=True,
        palette=["#9C6C6C", "#3A2A29"],  
        order=blocks,
        alpha=0.6,
        size=3,
        hue_order=grouped_dt["var_type"].unique()[::-1],
        ax=ax,
        legend=False,
    )
    ax.set_xlabel("Learn block")
    ax.set_ylabel("Fraction correct")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(blocks_short)
    ax.set_ylim(0.0, 1.25)

    handles, labels = ax.get_legend_handles_labels()
    label_map = {
        'rotational': 'Expt. 1',
        'unconstrained': 'Expt. 2'
    }
    new_labels = [label_map.get(label, label) for label in labels]
    ax.legend(handles, new_labels, title="")
    # ax.legend(title="")

    if hline is not None:
        ax.axhline(y=hline, linestyle="--", color="grey", alpha=0.7)

    return ax


# }}}
# Plot Congruency Task Analyses {{{


def axplot_task2_all(dt, key, descr="Fraction correct", verbose=0, ax=None, color=palette[3]):
    grouped_acc = dt.groupby(["subject_id"])[key].mean().reset_index()

    # Get Max values
    max_acc = grouped_acc[key].max()

    if ax is None:
        ax = plt.gca()

    sns.violinplot(
        grouped_acc,
        y=key,
        ax=ax,
        color=color[0],
        inner='quartile',
    )
    sns.stripplot(
        data=grouped_acc,
        y=key,
        dodge=True,
        jitter=True,
        color=color[1],
        alpha=0.7,
        ax=ax,
    )

    # Test against chance level and annotate
    chance_r = 0.5
    ttest = pg.ttest(dt.groupby("subject_id")[key].mean(), chance_r,)
    p_value_r = ttest["p-val"].iloc[0]
    print(ttest)
    ax.axhline(y=chance_r, color='grey', linestyle='--', alpha=0.7)

    sap.annot_stat_bar(sap.calc_stars(p_value_r),
                       -0.0, 1.17 * max_acc, ax=ax)

    ax.set_ylim([0,1.18])
    ax.set_ylabel(descr)
    ax.set_xlabel("")

    return ax



def axplot_task3_box_congr(dt, key, congruency_type, verbose=0,
                           ax=None):
    """Plot paired bars for congruence and incongruent acc/rt for all subjects according to a defined congruency type.
    """
    # Determine datatype
    if "rt" in key:
        dt_type = "rt"
    if "acc" in key:
        dt_type = "acc"

    dt.loc[:, "congr_type"] = dt[congruency_type].apply(
        lambda x: "congruent" if x == 1 else ("incongruent" if x == 0 else np.nan)
    )

    grouped_acc = dt.groupby(["subject_id", "congr_type"])[key].mean().reset_index()

    x = grouped_acc.query("congr_type == 'congruent'")[key]
    y = grouped_acc.query("congr_type == 'incongruent'")[key]
    ttest = pg.ttest(x, y, paired=True, r=0.707, alternative="greater") 
    t_result = [ttest["T"].iloc[0], ttest["p-val"].iloc[0]]
    d_cohen = ttest["cohen-d"].iloc[0]
    dof = ttest["dof"].iloc[0]
    bf_10 = float(ttest["BF10"].iloc[0])

    if verbose > 0:
        ps = "Paired"
        descr = dt_type
        print(
            f"\n{descr}: {ps} 1-sided t-test: t({dof}) = {t_result[0]:.2f}, p = {t_result[1]:.3f}"
            f"; Cohen's d = {d_cohen:.2f}"
        )
        if verbose > 1:
            print("Full result: ", ttest)

    if dt_type == "acc":
        chance = 0.5
        # Perform one-sample t-test against chance
        t_t, p_t = stu.test_against_chance(x, chance, label=descr)
        t_f, p_f = stu.test_against_chance(y, chance, label=descr)

    # Plot
    if ax is None:
        ax = plt.gca()

    sns.pointplot(
        grouped_acc,
        y=key,
        x="congr_type",
        order=["congruent", "incongruent"],
        color="black",
        ax=ax,
    )
    sns.stripplot(grouped_acc, x="congr_type", y=key, alpha=0.5,
                jitter=True, size=4, ax=ax,
                color="#3A2A29",
                order=["congruent", "incongruent"],
                )

    # Annotate with significance test between conditions
    max_acc = grouped_acc[key].max()
    annot = rf"{sap.calc_stars(t_result[1], near_to=True)}"
    sap.annot_stat(annot, 0, 1, 1.1 * max_acc, ax=ax)

    if dt_type == "acc":
        # Annotate with test against chance
        sap.annot_stat_bar(sap.calc_stars(p_t), 0, 1.05 * max_acc, ax=ax)
        sap.annot_stat_bar(sap.calc_stars(p_f), 1, 1.05 * max_acc, ax=ax)
        # Add Chance line
        ax.axhline(y=chance, color="grey", linestyle="--", alpha=0.5)

    # Draw Stripplot connections
    acc_congr = grouped_acc[grouped_acc["congr_type"] == "congruent"][key]
    acc_incongr = grouped_acc[grouped_acc["congr_type"] == "incongruent"][key]

    assert len(acc_congr) == len(acc_incongr), "Data not in same shape."
    sap.draw_stripplot_lines(acc_congr, acc_incongr, ax)

    # Other specs
    ax.set_ylim(0.0)
    ax.legend().set_visible(False)
    ax.set_xlabel("")

    gt = ">" if dt_type == "acc" else "<"  # rt
    ax.set_title(f"Exp.: {dt_type} congr {gt} incongr")
    ax.set_ylabel(f"mean subject {dt_type}")


# }}}
# Plot Mixed Effects Analyses {{{


def axplot_fixed_effects(
        effects, p_vals=None, errors=None, intercepts=False, p_val_pos=-3.8,
        skip_eucd=True, skip_wspd=True,
        ax=None, label_rotation=0, label_ha="center",
        rand_slope=False,
):
    """Plot result of fitted mixed effects model."""

    if ax is None:
        ax = plt.gca()

    effects = pd.melt(effects, var_name="predictor", value_name="value")
    effects_max = effects["value"].max()
    if intercepts is False:
        effects = effects[effects["predictor"] != "(Intercept)"]

    if errors is not None:
        effects_max += errors.max()
        effects["errors"] = effects["predictor"].apply(lambda x: errors.get(x))

    effects.reset_index(inplace=True, drop=True)


    if skip_wspd and skip_eucd:
        effects["wspd_pp_diff"] = np.nan
        new_row = {"predictor": "wspd_pp_diff", "value": 0, "error": 0}
        effects.loc[1] = new_row
        effects["eucd_pp_diff"] = np.nan
        new_row = {"predictor": "eucd_pp_diff", "value": 0, "error": 0}
        effects.loc[2] = new_row

    if skip_eucd and not skip_wspd:
        effects["eucd_pp_diff"] = np.nan
        new_row = {"predictor": "eucd_pp_diff", "value": 0, "error": 0}
        effects.loc[1] = new_row

    palette_list = list(dist_palette)  # start from base palette

    for preds in ({"spd_pp_diff", "subj_spd_pp_diff"}, {"spd_m_flat", "subj_spd_m_flat"}):
        if preds.issubset(effects["predictor"].values):
            palette_list.insert(1, "#a5c2d4")

    for preds in ({"eucd_pp_diff", "subj_eucd_pp_diff"}, {"eucd_m_flat", "subj_eucd_m_flat"}):
        if preds.issubset(effects["predictor"].values):
            palette_list.insert(3, "#ffe77dff")

    for preds in ({"wspd_pp_diff"}, {"wspd_m_flat",}):
        if preds.issubset(effects["predictor"].values):
            palette_list.insert(2, "#8bc865")   # green
    for preds in ({"wspd_pp_diff", "subj_wspd_pp_diff"}, {"wspd_m_flat", "subj_wspd_m_flat"}):
        if preds.issubset(effects["predictor"].values):
            palette_list.insert(2, "#a3e27c")   # green again (if you want both cases handled separately)



    palette = sns.color_palette(palette_list)

    sns.barplot(y="value", x="predictor", hue="predictor", data=effects,
                palette=palette, ax=ax,
                )
    ax.set_ylabel(r"Fixed Effect Estimate ($\beta$)")
    ax.set_xlabel("Predictor")

    # Add p values
    if skip_wspd:
        n = 2
        p_vals = pd.concat([p_vals.iloc[:n], 
                    pd.Series([np.nan], index=["wspd_pp_dist"]), 
                    p_vals.iloc[n:]])
    if skip_eucd:
        n = 2
        p_vals = pd.concat([p_vals.iloc[:n], 
                    pd.Series([np.nan], index=["eucd_pp_dist"]), 
                    p_vals.iloc[n:]])

    if p_vals is not None:
        if intercepts is False:
            p_vals = p_vals[p_vals.index != "(Intercept)"]
        for i, p_val in enumerate(p_vals):
            
            sap.annot_stat_bar(sap.calc_stars(p_val),
                               y=p_val_pos, x=i, rotation=0,
                               ax=ax)

    labels = format_labels(effects["predictor"].unique())
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=label_rotation, ha=label_ha)

    if rand_slope:
        sns.stripplot(
            y="value",
            x="predictor",
            data=effects,
            ax=ax,
            color="black",
            size=4,
            alpha=0.6,
            jitter=True,
            dodge=False,
            zorder=10,
        )

    # Add error bars
    if errors is not None:
        ax.errorbar(
            y="value",
            x="predictor",
            data=effects,
            yerr="errors",
            fmt=".",
            color="black",
            alpha=0.5,
        )


# }}}
# Plot task 4 analyses {{{


def axplot_heatmap(corr_m, labels, ax=None, cmap="coolwarm"):
    """Axplot a heatmap form a correlation matrix."""
    if ax is None:
        ax = plt.gca()

    cax = sns.heatmap(corr_m, annot=True, cmap=cmap, vmin=-1, vmax=1,
                      fmt='.2f', annot_kws={"size": 8}, cbar=False, ax=ax)
    # Set tick labels in center of each cell
    tick_positions = np.arange(len(labels)) + 0.5  # Shift by 0.5 to center
    ax.set_xticks(tick_positions)
    ax.set_yticks(tick_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, rotation=0, fontsize=9)
    ax.set_aspect('equal')

    return cax


def visualize_task4_predictors(dt, preds, subj_ind=0, cols=4, diagonal=True, seed=None):
    """Plot predictors as heatmap of the adjacency matrix."""
    dt = dt.drop_duplicates("subject_id").reset_index(drop=True)
    n_colors = ["#b1d5fe", "#77b5fe"]
    # Define grid size: limit to 5 columns
    n_cols = min(cols, len(preds))  # Max 5 columns
    n_rows = int(np.ceil(len(preds) / n_cols)) * 2  # Double rows for heatmaps & graphs

    fig, axs = plt.subplots(n_rows, n_cols, figsize=(n_cols * 2, n_rows * 2),
                            constrained_layout=True)

    for idx, pred in enumerate(preds):
        adj_m = dt["adj_m"].iloc[subj_ind]
        row, col = divmod(idx, n_cols)  # Calculate grid position
        ax = axs[row * 2, col]  # Heatmap position
        graph_ax = axs[row * 2 + 1, col]  # Graph position

        # Get label
        if pred.endswith("_flat"):
            label = pred[:-5]
        else:
            label = pred
        assert label.endswith("_m"), "Incorrect task4 predictor."

        # Determine color
        if label[:-2] in ["subj_spd", "subj_wspd", "subj_eucd",]:
            # node_color = "#bcdfff"
            node_color = n_colors[0]
        else:
            # node_color = "#8daccc"
            node_color = n_colors[1]

        # Plot
        try:
            dist_m = np.array(dt[label].iloc[subj_ind])
            dist_m /= dist_m.max()

            # Mask upper triangle (with or without diagonal)
            mask = np.triu(np.ones_like(adj_m), k=diagonal)

            # Plot heatmap
            img = sns.heatmap(dist_m, cbar=False, cmap="flare", mask=mask, ax=ax)
            ax.set_aspect('equal')
            ax.tick_params(axis='x', labelsize=7)
            ax.tick_params(axis='y', labelsize=7)
            ax.set_title(label[:-2].replace("_", " ").title(), fontsize=9)
            # Compute MDS and plot graph
            pos = sdu.run_mds(dist_m, nb_dim=2, seed=seed)
            spg.axplot_graph(adj_m, pos=pos, node_color=node_color, ax=graph_ax)
        except KeyError:
            ax.set_visible(False)
            graph_ax.set_visible(False)

    # Hide unused subplots (if any)
    for idx in range(len(preds), (n_rows * n_cols) // 2):
        row, col = divmod(idx, n_cols)
        axs[row * 2, col].axis("off")      # Hide heatmap subplot
        axs[row * 2 + 1, col].axis("off")  # Hide graph subplot

    # Create color bar
    cbar = fig.colorbar(img.collections[0], ax=[axs[0, 0], axs[0, cols-1]],
                        shrink=0.9, aspect=30)
    cbar.set_label("Distance", fontsize=12)

    return fig, axs


def get_corr_df(
    df, var_type,
    key1="subj_eucd_m_flat", key2="subj_spd_m_flat",
    corr_method="spearman",
):
    return (
        df.groupby("subject_id")[[key2, key1]]
          .corr(method=corr_method)
          .reset_index()
          .query(f"level_1 == @key1 and {key2} != 1.0")
          .assign(var_type=var_type)
          .rename(columns={key2: "subj_corr"})
          .drop(columns=["level_1", key1])
    )


def fisher_mean_r(vals):
    vals = np.asarray(vals, float)  # ensure a float numpy array
    z = np.arctanh(np.clip(vals, -0.999999, 0.999999)) # Fisher z-transform (clip to avoid ±∞)
    return np.tanh(np.nanmean(z))  # average on z, back-transform to r

def fisher_z(arr):
    return np.arctanh(arr)


def axplot_corrs_by_subj(corr_df, verbose=True, ax=None):
    rot = corr_df.query("var_type == 'rotational'")['subj_corr']
    unc = corr_df.query("var_type == 'unconstrained'")['subj_corr']
    # Fisher z transform
    rot = np.arctanh(rot)
    unc = np.arctanh(unc)
    altern = "two-sided"
    # altern = "less"
    test = pg.ttest(rot, unc, correction="auto", alternative=altern)
    # test = pg.mwu(rot, unc, alternative=altern)
    if verbose:
        print(test)

    if ax is None:
        ax = plt.gca()
    # sns.violinplot(
        # inner="quartile",
    sns.pointplot(
        color="#3d2c2c",
        data=corr_df, x="var_type", y="subj_corr",
        alpha=0.99,
        zorder=9,
        estimator=fisher_mean_r,
        n_boot=5000, 
        dodge=True,
        ax=ax)
    sns.stripplot(corr_df, x="var_type", y="subj_corr",
                  palette=dark_orange_palette,
                  hue="var_type",
                  alpha=0.6,
                  color="gray",
                  ax=ax)
    sap.annot_stat(rf"{sap.calc_stars(test["p-val"].iloc[0], near_to=True)}",
                   0, 1, 1.1, fontsize=9, ax=ax)
    ax.set_ylim([-1, 1.26])
    ax.set_xlabel("")
    ax.set_ylabel(r"Spearman's $\rho$")


def corr_df_to_latex(
    corr_df: pd.DataFrame,
    float_format: str = ".2f",
    caption: str | None = None,
    label: str | None = None,
    lower_triangle: bool = False,
    na_rep: str = "",
    latex_labels: bool = True,
    extended_labels: bool = True,
    compact: bool = True,
    rotate_headers: bool = True,
    header_angle: int = 60,
) -> str:
    """
    Convert a correlation matrix DataFrame to a LaTeX table string.

    - Uses format_label() for row/column labels.
    - Optionally blanks the lower triangle.
    - Optionally rotates column labels with \\rotatebox{angle}{...}
      to save horizontal space.
    - Uses compact spacing if compact=True.
    """

    # --- Format labels with your helper ---
    raw_cols = list(corr_df.columns)
    raw_rows = list(corr_df.index)

    col_labels = [
        format_label(c, extended=extended_labels, latex=latex_labels)
        for c in raw_cols
    ]
    row_labels = [
        format_label(r, extended=extended_labels, latex=latex_labels)
        for r in raw_rows
    ]

    df = corr_df.copy()

    # --- Optional lower triangle masking ---
    if lower_triangle:
        mask = np.tril(np.ones(df.shape, dtype=bool), k=-1)
        df = df.mask(mask)

    # --- Format numeric entries ---
    def _fmt(x):
        if pd.isna(x):
            return na_rep
        return format(x, float_format)

    df_fmt = df.applymap(_fmt)

    # --- Column spec: left label + right-aligned numeric columns ---
    n_cols = len(col_labels)
    col_spec = "l" + "r" * n_cols

    lines: list[str] = []
    lines.append("\\begin{table}[h!]")
    lines.append("\\centering")

    if compact:
        lines.append("\\scriptsize")
        lines.append("\\setlength{\\tabcolsep}{2pt}")
        lines.append("\\renewcommand{\\arraystretch}{1.1}")

    if caption:
        # For SI: often use caption* (unnumbered)
        lines.append(f"\\caption*{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")

    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\hline")

    if rotate_headers:
        header_cells = [
            rf"\makebox[0pt][l]{{\rotatebox[origin=l]{{{header_angle}}}{{{lbl}}}}}"
            for lbl in col_labels
        ]
    else:
        header_cells = col_labels

    header_line = " & " + " & ".join(header_cells) + " \\\\"
    lines.append(header_line)
    lines.append("\\hline")

    # --- Body rows ---
    for row_label, row_vals in zip(row_labels, df_fmt.values):
        line = row_label + " & " + " & ".join(row_vals) + " \\\\"
        lines.append(line)

    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def run_k_means(X, k_values, n_init=20):
    """Run k means clustering algorithm over range of dimensions and with different initializations."""
    inertia = []
    centroids = []
    labels = []

    for k in k_values:
        # Run k means 10 times with initialization
        kmeans = KMeans(n_clusters=k, init="k-means++", n_init=n_init)
        kmeans.fit(X)
        inertia.append(kmeans.inertia_)
        centroids.append(kmeans.cluster_centers_)
        labels.append(kmeans.labels_)

    return inertia, centroids, labels


def axplot_2d_congr_kM_clustering(
        dt: pd.DataFrame(), key: str, congruence_type: str, k: int,
        ax=None, verbose=0,
):
    """Plot a k-means clustering."""
    # It can happen that one group is empty for a congr_type, in that case
    # delete the subject beforehand (see function: axplot_task3_box_congr
    # for similar procedure)
    dt.loc[:, "congr_type"] = dt[congruence_type].apply(
        lambda x: "congruent" if x else "incongruent"
    )
    excl_subjs = []
    grouped_count = dt.groupby(["subject_id", "congr_type"])[key].count().reset_index()
    for subj, subj_count in grouped_count["subject_id"].value_counts().items():
        if subj_count != 2:
            excl_subjs.append(subj)
            if verbose >= 1:
                print(f"Subj excluded: {subj}, with count 0 for one of the categories.")
    for _, (subj, count) in grouped_count[["subject_id", key]].iterrows():
        if count < 5:
            excl_subjs.append(subj)
            if verbose >= 1:
                print(f"Subj excluded: {subj}, with count {count} for one of the categories.")
    if excl_subjs:  # check if list is non-empty
        print(f"{len(excl_subjs)} subjects excluded because of no/not enough data for one of the categories.")

    dt = dt[~dt["subject_id"].isin(excl_subjs)]

    # Get data and cluster
    subjs = dt["subject_id"].unique().tolist()
    cluster_dt = dt.groupby(["subject_id", "congr_type"])[key].mean()

    X = []
    for subj in subjs:
        df = cluster_dt.loc[subj]
        X.append(list(df.to_numpy())[::-1])
    X = np.array(X)[:, ::-1]  # reverse columns

    k_values = range(1, 11)
    inertia, centroids, labels = run_k_means(X, k_values)

    # Plot
    if ax is None:
        ax = plt.gca()

    chance = 0.5
    ax.axvline(chance, linestyle="--", color="grey", alpha=0.5, label="Chance")
    ax.axhline(chance, linestyle="--", color="grey", alpha=0.5)
    ax.plot(np.arange(0, 1.05, 0.01), np.arange(0, 1.05, 0.01),
            linestyle=":", color="grey", alpha=0.4,
            label="Equality")

    x_dt = pd.DataFrame({"congruent acc": X[:, 0], "incongruent acc": X[:, 1],
                         "cluster": labels[k-1]})
    sns.scatterplot(x_dt, x="congruent acc", y="incongruent acc",
                    color=dark_brown_palette[0],
                    legend=False,
                    s=70, alpha=0.75, ax=ax)
    # Plot mean
    ax.scatter(np.mean(X[:, 0]), np.mean(X[:, 1]), marker="o", s=70,
               facecolors='none', edgecolor='black', linewidth=1,
               label="Centroid")
    ax.set_title(f"K-means with k={k}")
    ax.set_ylabel("Incongruent fraction correct")
    ax.set_xlabel("Congruent fraction correct")

    ax.set_xlim([0, 1.05])
    ax.set_ylim([0, 1.05])
    ax.set_aspect('equal')
    ax.legend()

    return pd.DataFrame({"subject_id": subjs, "labels": labels[k-1]})

# }}}


if __name__ == "__main__":
    pass
