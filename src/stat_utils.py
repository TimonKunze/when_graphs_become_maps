import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import pingouin as pg
from scipy import stats
import statsmodels.api as sm
from itertools import combinations
from statsmodels.stats.outliers_influence import variance_inflation_factor
from matplotlib.offsetbox import AnchoredText

import src.distance_utils as sdu
# Cohen's d, Cosine Similarity {{{


def cohen_d(sample1, sample2, paired=True):
    """Calculate Cohen's d for two samples.

    Parameters:
    sample1 (pandas.Series or list): First sample data.
    sample2 (pandas.Series or list): Second sample data.

    Returns:
    float: Cohen's d effect size.
    """
    cohen_d = pg.compute_effsize(sample1, sample2, paired=paired,
                                 eftype='cohen')

    return cohen_d



# }}}
# Plot Correlations {{{


def calc_correlation(x, y, method="spearman"):
    """Calculate correlation, default is spearman."""
    if method == "spearman" or method == "s":
        corr = stats.spearmanr(x, y)[0]
        pval = stats.spearmanr(x, y)[1]
    elif method == "pearson" or method == "p":
        corr = stats.pearsonr(x, y)[0]
        pval = stats.pearsonr(x, y)[1]
    else:
        corr = np.corrcoef(x, y)[0][1]
        pval = np.nan

    return corr, pval


def fisher_z(r):
    """Apply Fisher z-transformation (e.g. to correlation coefficients).

    Correlation coefficients r are not normally distributed, especially
    when ∣r∣ is near 1 or the sample size is small. Their variance depends
    on both the sample size and the true correlation.

    To fix this, the Fisher z-transformation is applied:
        z=(1/2) * ln⁡((1+r)/(1−r))

    This transformation:
    - Makes the distribution of z approximately normal.
    - Provides approximately constant variance, independent of the true
      correlation.
    - Is particularly useful when comparing or averaging correlations.
    """
    r = np.clip(r, -0.999999, 0.999999)  # avoid division by zero
    return 0.5 * np.log((1 + r) / (1 - r))


def inverse_fisher_z(z):
    """Convert z back to correlation coefficient."""
    return np.tanh(z)


def string_corr_val(corr_val):
    """Correlation value in apa style.

    :param corr_val: int
    :return: string
    """
    if corr_val >= 0:
        string = str(np.round(corr_val, 2)).lstrip("0")
    else:
        string = str(abs(np.round(corr_val, 2))).lstrip("0")
        string = "–" + string

    return string


def string_p_val(p_val):
    """P-value in apa style.

    :param p_val: int
    :return: string
    """
    if p_val > 0.01:
        string = f"p = {p_val:.2f}".lstrip("0")
    elif 0.01 >= p_val >= 0.001:
        string = f"p = {p_val:.3f}".lstrip("0")
    else:
        string = "p < .001"

    return string


def plot_corr_matrix(
    df, method="pearson", labels=None, vmin=-1, vmax=1, cbar=True, ax=None
):
    """
    Plots the correlation matrix for a given pandas DataFrame.

    Parameters:
    df (pandas.DataFrame): The input dataframe.
    method (str): The correlation method to use (default is 'pearson').
                  Options: 'pearson', 'kendall', 'spearman'.
    """
    if ax is None:
        ax = plt.gca()

    corr_matrix = df.corr(method=method)
    if labels is not None:
        sns.heatmap(
            corr_matrix,
            annot=True,
            cmap="coolwarm",
            center=0,
            fmt=".2f",
            xticklabels=labels,
            yticklabels=labels,
            cbar=cbar,
            square=True,
            linewidths=0.5,
            vmin=vmin,
            vmax=vmax,
            ax=ax,
        )
    else:
        sns.heatmap(
            corr_matrix,
            annot=True,
            cmap="coolwarm",
            center=0,
            fmt=".2f",
            cbar=cbar,
            square=True,
            linewidths=0.5,
            vmin=vmin,
            vmax=vmax,
            ax=ax,
        )


# }}}
# Calculate and plot Regression {{{


def calc_vif(X: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor (VIF) for features in a DataFrame.

    VIF = 1: No shared variance
    VIF = 2: 50% of variance is shared
    VIF = 5: 80% of variance is shared
    VIF = 10: 90% of variance is shared
    """
    X = sm.add_constant(X)  # Add intercept
    vif_data = pd.DataFrame({
        "Variable": X.columns,
        "VIF": [variance_inflation_factor(X.values, i)
                for i in range(X.shape[1])]
    })

    return vif_data


def axplot_vif(vif_dt, ax=None, title=True):
    """Plot Variance Inflation Factor from data frame."""
    if ax is None:
        ax = plt.gca()

    sns.barplot(x="VIF", y="Variable", data=vif_dt, color="skyblue", orient="h", ax=ax)
    ax.axvline(x=1, color="green", linestyle="--", label="VIF>1")
    ax.axvline(x=5, color="orange", linestyle="--", label="VIF>5")
    ax.axvline(x=10, color="red", linestyle="--", label="VIF>10")
    if title:
        ax.set_title("Variance Inflation Factor")
    ax.set_xlabel("Predictors")
    ax.set_ylabel("VIF Value")
    ax.legend()


def calc_condition_nb(dt):
    """Calculate condition number to diagnose multicollinarity issues.

    < 10    No noticeable multicollinearity issues.
    10–30   Moderate multicollinearity; results may be affected.
    > 30    Severe multicollinearity; regression coefficients may be unreliable.
    > 100   Extreme multicollinearity; the design matrix is nearly singular, and results are likely invalid.
    """
    _, s, _ = np.linalg.svd(dt)  # Singular Value Decomposition
    condition_number = s.max() / s.min()
    return condition_number


def axplot_cond_nb(c_nb, ax=None, title=True):
    if ax is None:
        ax = plt.gca()
    thresholds = [10, 30, 100]
    colors = ["green", "orange", "red"]

    ax.bar(["Condition Number"], [c_nb], color="skyblue", width=0.5)
    for thresh, color in zip(thresholds, colors):
        ax.axhline(
            y=thresh, color=color, linestyle="--", label=rf"$\kappa$>{thresh}"
        )
    if title:
        ax.set_title(rf"Condition nb. $\kappa$={c_nb:.2f}")
    ax.set_ylabel(r"$\kappa$")
    ax.set_label("")
    ax.legend()


def calc_pearsson_residuals(model, y_key="response"):
    """Calculate Pearsson residuals."""
    numer = model.data[y_key] - model.fits
    denum = np.sqrt(model.fits * (np.array([1.0] * len(model.fits)) - model.fits))
    return numer / denum


def axplot_density(dt, ax=None):
    if ax is None:
        ax = plt.gca()

    sns.kdeplot(dt, fill=True, ax=ax)
    ax.set_xlabel("Residuals")
    ax.set_ylabel("Density")
    return ax


def axplot_qqplot(dt, ax=None):
    if ax is None:
        ax = plt.gca()

    qq = stats.probplot(dt, dist="norm")  # Compare with normal distribution
    theoretical_quantiles = qq[0][0]
    sample_quantiles = qq[0][1]
    sns.scatterplot(
        x=theoretical_quantiles,
        y=sample_quantiles,
        color="blue",
        label="Sample Data",
        ax=ax,
    )
    sns.lineplot(
        x=theoretical_quantiles,
        y=theoretical_quantiles,
        color="red",
        linestyle="--",
        label="Ideal Fit",
        ax=ax,
    )
    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Sample Quantiles")

    return ax


def plot_residuals(residuals):
    """Plot residuals, determining normality."""
    stat, p = stats.shapiro(residuals)

    fig, axs = plt.subplots(1, 2, figsize=(5, 2.5))
    axplot_density(residuals, axs[0])
    axplot_qqplot(residuals, axs[1])
    if p > 0.05:
        res = "--> normal"
    else:
        res = "--> not normal"
    plt.suptitle(f"SW test W={stat:.2f}, {string_p_val(p)}, {res}")
    plt.tight_layout()

    return fig, axs


# }}}
