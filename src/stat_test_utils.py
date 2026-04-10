import numpy as np
import pandas as pd
import pingouin as pg

from scipy import stats

import src.stat_utils as ssu


def format_number(x, threshold_upper=1e6, threshold_lower=1e-3, decimals=2):
    """Format a number as fixed-point or scientific notation depending on magnitude.

    Parameters:
        x (float): The number to format
        threshold_upper (float): Use scientific if |x| >= threshold_upper
        threshold_lower (float): Use scientific if |x| <= threshold_lower (nonzero)
        decimals (int): Number of decimals for fixed-point or scientific

    Returns:
        str: Formatted string
    """
    if x == 0:
        return f"{0:.{decimals}f}"  # zero always fixed-point

    if abs(x) >= threshold_upper or abs(x) <= threshold_lower:
        return f"{x:.{decimals}e}"  # scientific notation
    else:
        return f"{x:.{decimals}f}"  # fixed-point


def format_p(p_val, include_p=True):
    """Format a p-value for reporting in text."""
    if p_val < 0.001:
        if include_p:
            return "p < .001"
        else:
            return ".001"
    else:
        if include_p:
            return f"p = {p_val:.3f}".lstrip("0")
        else:
            return f"{p_val:.3f}".lstrip("0")


def format_bayes_factor(bf, bf_type="10", show_prior=False, bf_prior=0.707):
    """
    Format a Bayes Factor for reporting.

    Parameters
    ----------
    bf : float
        The Bayes Factor value.
    bf_type : str, optional
        Type of Bayes Factor: "10" for BF10, "01" for BF01. Default is "10".
    show_prior : bool, optional
        Whether to include the prior scale in the output. Default is False.
    bf_prior : float, optional
        Scale of the Cauchy prior. Default is 0.707.

    Returns
    -------
    str
        Formatted Bayes Factor string for reporting.
    """
    bf_str = format_number(
        bf, threshold_upper=1e6, threshold_lower=1e-3, decimals=2)

    bf_label = f"$\text{{BF}}_{{{bf_type}}} = {bf_str}$"

    if show_prior:
        bf_label += f" ($r = {bf_prior}$)"

    return bf_label


def stat_report(test, report_d=True, bf_r_val=0.707,):
    """Return LaTeX-formatted statistics report from a Pingouin t-test result.

    Parameters:
        test (pd.DataFrame): Output of pingouin.ttest()
        bf_r_val (float): Bayes factor prior scale (default=0.707)
        report_d (bool): Whether to include Cohen's d
    """
    row = test.iloc[0]  # Get first result row
    t_val = row['T']
    dof = int(round(row['dof']))
    p_val = row['p-val']
    bf10 = float(row['BF10'])
    cohen_d = row['cohen-d']

    # Format p-value
    show_prior = False
    if not isinstance(bf_r_val, float):
        show_prior = True

    p_str = format_p(p_val)
    bf_str = format_bayes_factor(
        bf10, show_prior=show_prior, bf_prior=bf_r_val)

    # Build report string
    stat_str = (
        f"$t({dof}) = {t_val:.2f}$, "
        f"${p_str}$, "
        f"{bf_str}"
    )

    if report_d:
        stat_str += f", $d = {cohen_d:.2f}$"

    return stat_str


def report_skewed_distribution(x, digits=2, na_rm=True, style="range"):
    """Summarize a (possibly skewed) distribution with Median and IQR.

    Parameters
    ----------
    x : array-like
        Data vector.
    digits : int
        Decimal places in the report.
    na_rm : bool
        If True, drop NaNs.
    style : {"range", "width"}
        "range" -> IQR reported as "Q1–Q3"
        "width" -> IQR reported as a single width value (Q3 - Q1)

    Returns
    -------
    str
        Formatted APA-style friendly string, e.g.:
        "Mdn = 5.20, IQR = 3.00–8.10 (n = 120)"
    """
    x = np.asarray(x, dtype=float)
    if na_rm:
        x = x[~np.isnan(x)]
    n = x.size
    if n == 0:
        return "No data (n = 0)."

    q1, med, q3 = np.percentile(x, [25, 50, 75])
    iqr = q3 - q1

    if style == "width":
        return f"Mdn = {med:.{digits}f}, IQR = {iqr:.{digits}f} (n = {n})"
    else:  # "range"
        return f"Mdn = {med:.{digits}f}, IQR = {q1:.{digits}f}–{q3:.{digits}f} (n = {n})"


def print_mean_and_std(df, brackets=True, latex=False):
    """Print mean and standard deviation for each column in pandas Series or DataFrame.

    Parameters:
        df (pandas.Series or pandas.DataFrame): Input data to calculate mean and SD.
        remove_brackets (bool): Whether to remove the brackets around the values.
        latex (bool): Whether to format the output for LaTeX math mode.
    """
    # Function to format the output
    def format_output(mean, std):
        if latex:
            return f"$M = {mean:.2f}$, $SD = {std:.2f}$"
        else:
            if brackets:
                return f"(M = {mean:.2f}, SD = {std:.2f})"
            else:
                return f"M = {mean:.2f}, SD = {std:.2f}"

    # If input is pandas Series
    if isinstance(df, pd.Series):
        mean = df.mean()
        std = df.std()
        print(format_output(mean, std))
    # If input is pandas DataFrame
    elif isinstance(df, pd.DataFrame):
        for col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            print(f"{col}: {format_output(mean, std)}")
    # Handle unknown or unsupported input types
    else:
        print("Unknown input type. Provide a pandas Series or DataFrame.")


def compare_groups_t_test(dt, cond_key, value, subj_key="subject_id", verbose=0,
                          descr="", paired=False):
    """Perform an t-test and compute Cohen's d between two conditions in a dataset.

    This function extracts two unique conditions from the specified column (`cond_key`)
    in the dataset (`dt`), retrieves their corresponding values (`value`), and performs
    an independent two-sample t-test (`ttest_ind`). It also computes Cohen's d to quantify
    the effect size.

    Parameters:
    -----------
    dt : pandas.DataFrame
        The dataset containing the conditions and values.
    cond_key : str
        The column name in `dt` that specifies the grouping variable (e.g., condition or group).
    value : str
        The column name in `dt` containing the numerical values to compare.
    verbose : int, optional (default=0)
        Controls the verbosity of output:
        - `0`: No output.
        - `1`: Prints a summary of the test results.
        - `2`: Prints a detailed output including full test results.
    descr : str, optional (default="")
        A description or label for the test (useful when printing results).

    Notes:
    ------
    - Assumes `cond_key` has exactly two unique values.
    - Drops NaN values before performing the t-test.
    - Uses an independent t-test (`ttest_ind`) by default, as a paired t-test (`ttest_rel`)
      is not applicable when sample sizes are unequal.
    """
    N = len(dt[subj_key].unique())
    cond1, cond2 = dt[cond_key].unique().tolist()
    cond1_dt = dt[dt[cond_key] == cond1][value].dropna()
    cond2_dt = dt[dt[cond_key] == cond2][value].dropna()
    if paired:
        t_test = stats.ttest_rel(
            cond1_dt, cond2_dt
        )  # Paired t-test doesn't work inequal array lengths
    else:
        t_test = stats.ttest_ind(cond1_dt, cond2_dt)  # drop for nans

    cohen_d = ssu.cohen_d(cond1_dt, cond2_dt, paired=paired)

    if verbose > 0:
        if paired:
            ps = "Paired"
        else:
            ps = "Independent"
        print(
            f"\n{descr}: {ps} t-test: t({N-1}) = {t_test[0]:.2f}, p = {t_test[1]:.3f}, 1-side p = {t_test[1]/2:.3f}; Cohen's d = {cohen_d:.2f}"
        )
        if verbose > 1:
            print("Full result: ", t_test)

    return t_test, cohen_d


def test_against_chance(data, chance=0.5, label="", 
                        alternative="two-sided", verbose=1):
    """Perform t test against chance."""
    ttest = pg.ttest(data, chance, alternative=alternative, r=0.707)
    t, p = ttest["T"].iloc[0], ttest["p-val"].iloc[0]
    if verbose > 0:
        print(
            f"\n{label}: {alternative} t-test against chance ({chance:.2f}): "
            f"t({ttest['dof'].iloc[0]}) = {t:.4f}, p = {p:.4f}"
        )
        if verbose > 1:
            print(ttest)
    return t, p

