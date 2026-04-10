#!/usr/bin/env python3
import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import zscore
from pymer4.models import Lmer
from numpy.linalg import LinAlgError

import src.stat_utils as ssu
import src.stat_test_utils as stu
import src.plot_analysis as spa

from src.plot_analysis import format_label
from src.stat_test_utils import format_p


# Get Mixed Model data set
def prepare_mm3_dt(task3_4_data, zscore_flag=True):
    """Prepare dataset to predict left-right response in task 3."""
    d_cols = [col for col in task3_4_data.columns if col.endswith("_pp_diff")]
    extra_cols = ["subject_id", "response", "var_type"]
    mm3_df = task3_4_data[d_cols + extra_cols].copy()
    # Clean data by dropping nan and inf values
    mm3_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    categoric_predictors = ["spd_pp_diff", "subj_spd_pp_diff"]
    d_cols_no_cp = [el for el in d_cols if el not in categoric_predictors]
    if zscore_flag:
        # Z-score predictors (but subject_id, response column, categorical preds)
        mm3_df[d_cols_no_cp] = zscore(mm3_df[d_cols_no_cp], nan_policy='omit')
    else:
        # Just scale predictors by std to preverve original mean
        mm3_df[d_cols_no_cp] = mm3_df[d_cols_no_cp] / mm3_df[d_cols_no_cp].std()

    # Invert response so that 0 is right response correct and 1 is left response correct
    mm3_df["response"] = np.abs(mm3_df["response"] - 1)

    first_half_mask = task3_4_data["trial_ind_congrtest"] < 32
    mm3_df["trial_split"] = (
        first_half_mask
        .map({True: "first_half", False: "second_half"})
        .astype("category")
    )

    return mm3_df


def prepare_mm4_dt(task4_dt, zscore_flag=True):
    if (task4_dt["var_type"] == "unconstrained").any():
        # drop columns that are nan in experiment 2
        task4_dt = task4_dt.drop(
            columns=["wspd_m_flat",	"eucd_m_flat",	"cosd_m_flat","cosw_spd_m_flat"]
        )

    num_cols = task4_dt.filter(regex="_flat$").columns.tolist()
    cols = (num_cols + ["subject_id", "var_type"])
    task4_dt= task4_dt[cols]

    exclude_cols = {"subject_id", "var_type"}
    m_cols = [col for col in task4_dt.columns if col not in exclude_cols]

    mm4_dt = task4_dt.explode(m_cols)  # explode lists
    mm4_dt[num_cols] = mm4_dt[num_cols].apply(pd.to_numeric, errors="coerce") # convert flat columns to numeric 

    if zscore_flag:
        mm4_dt[num_cols] = mm4_dt[num_cols].apply(zscore, nan_policy="omit")  # standardize 

    return mm4_dt


def plot_vif_and_cond_nb(dt, **kwargs):
    """Plot variance inflation factor and condition number."""
    fig, axs = plt.subplots(1, 2, figsize=kwargs.pop("figsize", (7, 2.5)))
    try:
        condition_number = ssu.calc_condition_nb(dt)
        vif_data = ssu.calc_vif(dt)
        ssu.axplot_vif(vif_data, axs[0], **kwargs)
        ssu.axplot_cond_nb(condition_number, ax=axs[1], **kwargs)
    except LinAlgError:
        print("Passed exception because of LinAlgError: SVD did not converge")
    plt.tight_layout()
    return fig, axs


def df_to_vif_latex(df, caption="Variance Inflation Factors", label="tab:vif"):
    """
    Convert a DataFrame of VIFs to a LaTeX table.
    Uses format_label(..., latex=True) to format predictor names.
    Automatically applies makecell for line breaks.
    """
    # Remove intercepts / constants
    df_clean = df[~df['Variable'].str.lower().isin(['const', 'intercept'])].copy()

    # Format predictor names using YOUR function
    df_clean["Label"] = df_clean["Variable"].map(
        lambda x: format_label(x, extended=True, latex=True)
    )

    latex = (
        "\\begin{table}[h!]\n"
        "\\centering\n"
        "\\footnotesize\n"
        "\\renewcommand{\\arraystretch}{1.2}\n"
        f"\\caption*{{\\textbf{{{caption}}}}}\n"
        "\\begin{tabular}{l c}\n"
        "\\hline\n"
        "\\textbf{Predictor} & \\textbf{VIF} \\\\\n"
        "\\hline\n"
    )

    for _, row in df_clean.iterrows():
        # Make predictor names breakable if needed
        pred = f"\\makecell[l]{{{row['Label']}}}"
        vif = f"{row['VIF']:.3f}"
        latex += f"{pred} & {vif} \\\\\n"

    latex += (
        "\\hline\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )

    return latex


def format_model_results(results, row_ind=0):
    """Print model results to be copied in results section."""
    print(results.index[row_ind])
    row = results.iloc[row_ind]

    results_str = (
        f"$\\beta = {row['Estimate']:.2f}$, "
        f"SE = {row['SE']:.2f}, "
        f"z = {row['Z-stat']:.2f}, "
        f"${stu.format_p(row['P-val'])}$"
    )
    print(results_str)


def run_mixed_model(
    dt,
    predictors,
    y="response",
    interaction=False,
    group_interaction=None,
    extra=None,
    rand_slope=False,
    family="binomial",
    bootstrap=False,
    n_boot=500,
    seed=None,
    summarize=True,
    plotting=1,
    save_as=None,
    label_rotation=15,
    skip_eucd=False,
    skip_wspd=False,
    label_ha="center",
):
    """Run the mixed model with certain specs given data and predictors."""
    if group_interaction is not None:
        pred_star = [f"{p} * {group_interaction}" for p in predictors]
    else:
        pred_star = predictors
    if interaction:
        pred_str = " * ".join(pred_star)
    else:
        pred_str = " + ".join(pred_star)

    if rand_slope is True:
        rand_slope_ins = pred_str
    else:
        rand_slope_ins = 1
    if extra is not None:
        pred_str += extra
    
    model = Lmer(
            f"{y} ~ {pred_str} + ({rand_slope_ins}|subject_id)",
            data=dt,
            family=family,
    )
    results = model.fit(summarize=summarize, 
                        conf_int="boot" if bootstrap else "Wald",
                        n_boot=n_boot, seed=seed)

    if plotting == 1 or plotting >= 2:
        fig, ax = plt.subplots(1, 1)
        if rand_slope:
            errors = None
        else:
            errors=results["SE"]

        spa.axplot_fixed_effects(
            model.fixef,
            errors=errors,
            p_vals=results["P-val"],
            p_val_pos=0.005,
            label_rotation=label_rotation,
            skip_eucd=skip_eucd,
            skip_wspd=skip_wspd,
            ax=ax,
            rand_slope=rand_slope,
            label_ha=label_ha,
        )
        fig.tight_layout()
        if save_as is not None:
            fig.savefig(save_as)
        plt.show()

        # Correlate gen data with true data
        try:
            corr = scipy.stats.spearmanr(model.fits, dt[y])
            print(f"Corr. of true and gen data: spearm={corr[0]:.2f}, p_val={corr[1]:.4f}")
        except:
            print("correlation didn't")
            pass

    if plotting > 1:
        plot_vif_and_cond_nb(dt[predictors])
        plt.show()

        ssu.plot_residuals(model.residuals)
        plt.show()

    return model, results


def calc_fixef_predict(model):
    """Get predictions based only on fixed effects, by
    manually computing them using estimated fixed
    coefficients.
    """
    # Extract fixed effect coefficients (excluding intercept)
    fixed_effects = model.coefs["Estimate"].iloc[1:].values
    # Get intercept estimate
    interc = model.coefs.loc["(Intercept)", "Estimate"]
    # Extract fixed effect predictor values
    preds = model.fixef.columns
    if "(Intercept)" in preds:
        preds = preds.drop("(Intercept)")
    if "var_type" in preds:
        preds = preds.drop("var_type")
    X_fixed = model.data[preds].values
    # Compute fitted values using only fixed effects
    fitted_fixed = np.dot(X_fixed, fixed_effects) + interc

    return fitted_fixed


def icc_from_pymer(model):
    """ICC(1) based on the random intercept variance from a pymer4 Lmer object."""
    # Filter ranef_var to the intercept term
    ranef_df = model.ranef_var
    intercept_var = ranef_df.query("Name == '(Intercept)'")["Var"].to_numpy()

    resid_var = model.residuals.var(ddof=1)
    icc = intercept_var / (intercept_var + resid_var)
    return icc


def mm_results_to_latex(results, printing=True, caption="TBC", label="tab:mm"):
    """Format mixed model results as a LaTeX table.

    Assumes optional helper functions:
        - format_labels(name: str) -> str
        - format_p(p: float) -> str
    """
    results = results.copy()

    # Ensure predictor names are not lost (index -> column)
    if "Predictor" not in results.columns:
        results = results.reset_index().rename(columns={"index": "Predictor"})

    # ----- Logistic-type models with OR CI -----
    if "OR_2.5_ci" in results.columns:
        # Build CI column with escaped percent in the header
        results[r"95\% CI for OR"] = results.apply(
            lambda r: [r["OR_2.5_ci"], r["OR_97.5_ci"]], axis=1
        )

        # Drop unused columns
        results = results.drop(
            columns=[
                "Prob", "Prob_2.5_ci", "Prob_97.5_ci", "Sig",
                "2.5_ci", "97.5_ci",
                "OR_2.5_ci", "OR_97.5_ci",
            ],
            errors="ignore",
        )

        # Keep group (var_type) next to predictor
        if "var_type" in results.columns:
            results.insert(1, "var_type", results.pop("var_type"))

        # Put test stats next to beta
        if "Z-stat" in results.columns:
            results.insert(4, "Z-stat", results.pop("Z-stat"))
        if "P-val" in results.columns:
            results.insert(5, "P-val", results.pop("P-val"))

    # ----- Linear-type models with normal CI -----
    if "2.5_ci" in results.columns:
        # CI column with escaped percent
        results[r"95\% CI"] = results.apply(
            lambda r: [r["2.5_ci"], r["97.5_ci"]], axis=1
        )

        results = results.drop(
            columns=["Sig", "2.5_ci", "97.5_ci"],
            errors="ignore",
        )

        if "var_type" in results.columns:
            results.insert(1, "var_type", results.pop("var_type"))

        if "T-stat" in results.columns:
            results.insert(4, "T-stat", results.pop("T-stat"))
        if "P-val" in results.columns:
            results.insert(5, "P-val", results.pop("P-val"))

    # ----- Rename columns to LaTeX-friendly names -----
    results.rename(
        columns={
            "var_type": "Group",
            "P-val": "p",
            "Estimate": r"$\beta$",
        },
        inplace=True,
    )

    if "Z-stat" in results.columns:
        results.rename(columns={"Z-stat": "z"}, inplace=True)
    if "T-stat" in results.columns:
        results.rename(columns={"T-stat": "T"}, inplace=True)

    # ----- Apply label formatter to predictors -----
    # Format predictor names using LaTeX (Δ → $\Delta$)
    if "Predictor" in results.columns:
        results["Predictor"] = results["Predictor"].map(
            lambda x: format_label(x, extended=True, latex=True)
        )

    # ----- Apply p-value formatter -----
    if "p" in results.columns:
        # expects format_p(p: float) -> str
        results["p"] = results["p"].map(
            lambda x: format_p(x, include_p=False,)
        )

    # ----- Move OR to second-last column (before CI) if present -----
    if "OR" in results.columns:
        OR_col = results.pop("OR")
        results.insert(len(results.columns) - 1, "OR", OR_col)

    # ----- Build LaTeX -----
    # escape=False so $\beta$, \_, \% etc. are interpreted as LaTeX
    to_latex = results.to_latex(
        index=False,
        float_format="%.2f",
        caption=caption,
        label=label,
        escape=False,
    )

    # Replace booktabs rules with plain \hline (for PLOS-like styles)
    to_latex = (
        to_latex.replace(r"\toprule", r"\hline")
                .replace(r"\midrule", r"\hline")
                .replace(r"\bottomrule", r"\hline")
    )

    if printing:
        print(to_latex)

    return results


def table_from_df(df: pd.DataFrame,
                  ax: plt.Axes | None = None,
                  include_index: bool = True,
                  fontsize: int = 10,
                  zebra: bool = True,
                  cell_loc: str = "center"):
    """Render a pandas DataFrame as a matplotlib table on the provided Axes."""
    # Include index if needed
    if include_index:
        data = df.reset_index()
    else:
        data = df.copy()

    # ---- FIX STARTS HERE: move Z-stat and p columns to the end ----
    cols = list(data.columns)

    # Columns whose *lowercase name contains* "z" or which equal "p"
    move_last = [
        c for c in cols 
        if ("z" in c.lower()) or (c.lower() == "p")
    ]

    keep_first = [c for c in cols if c not in move_last]

    data = data[keep_first + move_last]
    # ---- FIX ENDS HERE ----

    col_labels = list(data.columns)
    cell_text = data.astype(str).values.tolist()

    # Create Axes
    if ax is None:
        ax = plt.gca()

    ax.set_axis_off()

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc=cell_loc,
        loc="center",
    )

    # Basic styling
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.25)

    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_text_props(weight="bold")
            cell.set_linewidth(1.25)
        else:
            if zebra and r % 2 == 0:
                cell.set_facecolor("#f6f6f6")

    return ax, table


def set_left_aligned_title(
        ax, fig=None, text="", y=1.05, fontsize=12, **kwargs):
    """Left-align a panel title."""
    if fig is None:
        fig = ax.figure

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label_x = ax.yaxis.get_tightbbox(renderer).xmin
    axes_x0 = ax.get_position().x0 * fig.get_size_inches()[0] * fig.dpi
    offset = (label_x - axes_x0) / (ax.get_position().width * fig.get_size_inches()[0] * fig.dpi)

    ax.text(
        offset, y, text,
        transform=ax.transAxes,
        ha="left", va="bottom",
        fontsize=fontsize,
        **kwargs
    )
    return ax


def plot_model_specs(data, results, model,
                     panel_nb=[
                         r"$\mathbf{(a)}$",
                         r"$\mathbf{(b)}$",
                         r"$\mathbf{(c)}$",
                         r"$\mathbf{(d)}$",
                         r"$\mathbf{(e)}$",
                     ],
                     height_ratios=[1.2, 0.35, 1],
                     fig_size=(10, 4),
                     ):
    """Plot mixed model specifications."""
    results_df = results.copy()
    predictors = results_df.index.drop("(Intercept)")
    predictor_labels = spa.format_labels(predictors)

    results_df.index = ["(Intercept)"] + predictor_labels
    results_df = mm_results_to_latex(results_df, printing=False)

    # Figure + GridSpec: 2 rows, 2 cols
    fig = plt.figure(figsize=fig_size)
    gs = fig.add_gridspec(nrows=3, ncols=2, height_ratios=height_ratios,
                          hspace=0.35, wspace=0.3)

    # Top: spans full row
    ax_top = fig.add_subplot(gs[0, :])
    ax_top_2 = fig.add_subplot(gs[1, :])

    # Bottom: two parallel subplots
    ax_bl = fig.add_subplot(gs[2, 0])
    ax_br = fig.add_subplot(gs[2, 1])

    # Optional: put them in a list for convenience
    axs = [ax_top, ax_top_2, ax_bl, ax_br]

    # --- Demo content ---
    axs[0], tbl = table_from_df(results_df, ax=axs[0], include_index=True)

    replacements = {
        "subj_wspd_pp_diff": "subj. wtd. path dist.\n",
        "wspd_pp_diff": "wtd. path dist.",
        "subj_spd_pp_diff": "subj. path dist.",
        "spd_pp_diff": "path dist.",
        "subj_eucd_pp_diff": "subj. Eucd. dist.",
        "eucd_pp_diff": "Eucd. dist.",
        "color_pp_diff": "color dist.",
        "response": "Right-side choice",
        "subject_id": "Participant",
        "+": " + ",
        "~": " ~ ",
    }
    replaced_formula = model.formula
    for old, new in replacements.items():
        replaced_formula = replaced_formula.replace(old, new)
    axs[1].axis("off")
    axs[1].text(0.5, 0.6, f"{replaced_formula}",
                ha="center", va="center", fontsize=10,)

    corr_m = data[predictors].corr().to_numpy()
    labels = spa.format_labels(data[predictors].columns)
    spa.axplot_heatmap(corr_m, labels=labels,
                       ax=axs[2], cmap="coolwarm")

    dt_vif = data[predictors]
    dt_vif.columns = predictor_labels
    vif_data = ssu.calc_vif(dt_vif)
    ssu.axplot_vif(vif_data, axs[3], title=False)

    set_left_aligned_title(
        axs[0], fig,
        panel_nb[0] + " Model results " + \
        f"(log-likelihood = {model.logLike:.1f}, AIC={model.AIC:.1f})",
        fontsize=12)
    set_left_aligned_title(
        axs[1], fig,
        panel_nb[1] + " Model R-formula",
        fontsize=12)
    set_left_aligned_title(
        axs[2], fig,
        panel_nb[2] + " Spearman correlations",
        fontsize=12)
    set_left_aligned_title(
        axs[3], fig,
        panel_nb[3] + " Variance inflation",
        fontsize=12)

    return fig
