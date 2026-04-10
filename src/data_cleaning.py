#!/usr/bin/env python3
"""Clean jsonl data and preprocess."""
import os
import re
import numpy as np
import pandas as pd

from functools import partial

import src.distance_utils as sdu

from src.config import PATHS


# Functions {{{

def rename_col_inplace(df, old_name, new_name):
    """Rename a column in a pandas DataFrame in place.
    """
    if old_name in df.columns:
        df.rename(columns={old_name: new_name}, inplace=True)
    else:
        raise ValueError(f"Column '{old_name}' does not exist in the DataFrame.")

# Create Data frames
def list_files(dir_path, file_type=""):
    """List files in a directory with specific filetype."""
    fs = os.listdir(dir_path)
    return [os.path.join(dir_path, f) for f in fs if f.endswith(file_type)]


def create_df_from_json_dir(dir_path):
    """Create pd dataframe from json files in directory."""
    dfs = []
    file_ending = ".jsonl"
    for f in list_files(dir_path, file_ending):
        try:
            dfs.append(pd.read_json(f, lines=True))
            print(f"Processing file: {f}")
        except ValueError as e:
            print(f"Skipping file {f} due to error: {e}")
    if dfs:
        return pd.concat(dfs, axis=0) if len(dfs) > 1 else dfs[0]
    return None


# Data cleaning functions
def arr_to_list(arr):
    """Convert numpy arrays to lists."""
    return arr.tolist()


def resolve_dict(group, trial_name, key_name=None):
    """Extract a specific value from the 'response' field of a given trial within a group.

    Parameters:
    - group (pd.DataFrame): Grouped DataFrame (e.g., from groupby).
    - trial_name (str): The name of the trial to filter on.
    - key_name (str, optional): The key to extract from the response dictionary.
                                If None, defaults to trial_name.

    Returns:
    - The extracted value, or the raw response if extraction fails.
    """
    if key_name is None:
        key_name = trial_name

    try:
        response = group.loc[group['trial_name'] == trial_name, 'response'].iloc[0]
        value = response.get(key_name) if isinstance(response, dict) else response
    except IndexError:
        value = np.nan

    return value


def trial_as_col_dt(df_old, df_new, trial_name, key_name):
    """Convert trials to columns in dataframe."""
    dt = df_old.groupby("subject_id").apply(
        lambda grp: resolve_dict(grp, trial_name, key_name),
        include_groups=False,
    )
    return df_new["subject_id"].map(dt)


def add_conf_ratings(df_old, df_new, var_type):
    """Add confidence ratings."""
    df_new["consc_confratings_" + var_type] = trial_as_col_dt(
        df_old, df_new, "conf_ratings_" + var_type, "consciousness")
    df_new["clar_confratings_" + var_type] = trial_as_col_dt(
        df_old, df_new, "conf_ratings_" + var_type, "clarity")
    df_new["diff_confratings_" + var_type] = trial_as_col_dt(
        df_old, df_new, "conf_ratings_" + var_type, "difficulty")
    df_new["conf_confratings_" + var_type] = trial_as_col_dt(
        df_old, df_new, "conf_ratings_" + var_type, "confidence")


# Convert reaction times to seconds
def convert_rt_to_seconds(data, key_startwith="rt"):
    """Convert reaction times to seconds."""
    rt_columns = [col for col in data.columns if col.startswith(key_startwith)]
    for rt in rt_columns:
        data[rt] = data[rt].apply(lambda x: x/1000)


def combine_date_time_row(row, list_idx=0, target_tz="Europe/Berlin"):
    # Expect row["date"] and row["time"] to be lists; take the first item
    if not row["date"] or not row["time"]:
        return pd.NaT

    # 1) Date as YYYY-MM-DD (avoid the embedded "00:00:00")
    date_str = pd.Timestamp(row["date"][list_idx]).strftime("%Y-%m-%d")

    # 2) Clean time string: drop "(...)" and literal "GMT"
    if "cheater" not in row.index and "age" not in row.index:
        # time_clean = pd.NaT
        return pd.NaT
    elif pd.notna(row["cheater"]) and pd.notna(row["age"]):  # if not nan
        time_raw = str(row["time"][list_idx])
        time_clean = re.sub(r"\s*\(.*\)$", "", time_raw)  # drop trailing "(...)"
        time_clean = re.sub(r"\s*GMT", "", time_clean, flags=re.I).strip()  # drop "GMT" (keep +0100 if present)
    else:  # if part 1 or 2 is not existent nan
        # time_clean = pd.NaT
        return pd.NaT

    dt_str = f"{date_str} {time_clean}"

    # 3) Parse: try with numeric tz offset (e.g., +0100), else plain HH:MM:SS
    try:
        ts = pd.to_datetime(dt_str, format="%Y-%m-%d %H:%M:%S%z", utc=True)  # aware in UTC
    except Exception:
        try:
            ts = pd.to_datetime(dt_str, format="%Y-%m-%d %H:%M:%S")  # naive
            ts = ts.tz_localize(target_tz).tz_convert("UTC")         # make it aware
        except Exception:
            return pd.NaT

    # Convert final display zone
    return ts.tz_convert(target_tz)


# }}}


def clean_all_data(pilot, var_type):
    """Clean and preprocess raw data for a datacollection and experiment type.

    This function performs several steps to clean and preprocess the data,
    including:
    1. Loading raw data from JSON files.
    2. Removing invalid subjects (e.g., test runs or undefined).
    3. Organizing data columns and reordering for better readability.
    4. Cleaning core data and task-specific data (task1, task2, task3, task4).
    5. Calculating total durations for learning and testing phases.
    6. Adding additional data such as cheater responses and converting time
       units.
    7. Saving the cleaned data into CSV files for further analysis.
    """
    # Load data
    # =========
    data = create_df_from_json_dir(
        PATHS[f'{pilot.replace("_", "")}-raw-{var_type}'])

    # Drop nan subjects if any (which are test runs)
    data = data[~data["subject_id"].isin([np.nan, "undefined"])]

    # Print info
    print("Number participants: ", len(data["subject_id"].unique()))
    print(list(data["subject_id"].drop_duplicates()))

    # Reorder trials (only for visualization)
    data.insert(0, "subject_id", data.pop("subject_id"))
    data.insert(1, "trial_name", data.pop("trial_name"))

    # Clean Data different task data separately
    # =========================================
    core_data = clean_core_data(data, var_type)
    task1_data = clean_task1_data(data)
    task2_data = clean_task2_data(data)
    task3_data = clean_task3_data(data)
    task4_data = clean_task4_data(data)

    # Save Data
    # =========
    save_path = PATHS[f'{pilot.replace("_", "")}-tidy-{var_type}']
    core_data.to_csv(save_path / "core_data.csv", index=False)
    task1_data.to_csv(save_path / "task1_data.csv", index=False)
    task2_data.to_csv(save_path / "task2_data.csv", index=False)
    task3_data.to_csv(save_path / "task3_data.csv", index=False)
    task4_data.to_csv(save_path / "task4_data.csv", index=False)


def clean_core_data(data, var_type):
    # Define columns
    agg_dict = {
        # General
        "date": list,
        "time": list,
        "group_name": "first",
        "study_id": "first",
        "session_id": "first",
        # Animation Environment
        "node_positions": "first",
        "canvas_size": "first",
        "node_size": "first",
        "node_paths": "first",
        # Learning
        "nb_learn_passes": "first",
        "nb_learn_blocks": "first",
        "nb_relation": "first",
        "nb_learn_trials_in_block": "first",
        "nb_learn_trials": "first",
        "relations": "first",
        # Graph Matrices
        "adjacency_matrix": "first",
        # Congruency
        "eucd_congr_pairs": "first",
        "eucd_incongr_pairs": "first",
        "wspd_congr_pairs": "first",
        "wspd_incongr_pairs": "first",
        "test3_pairs": "first",
        "time_elapsed": "max",
        # Flags
        "debug_flag": "first",
        "rand_flag": "first",
        "part1_flag": "first",
        "part2_flag": "first",
        "prolific_flag": "first",
        "feedback_flag": "first",
    }
    # Filter to only use available columns and aggregate
    agg_dict_filtered = {k: v for k, v in agg_dict.items() if k in data.columns}
    core_data = data.groupby("subject_id").agg(agg_dict_filtered).reset_index()
    # Add missing columns as NaN
    missing_cols = [col for col in agg_dict if col not in core_data.columns]
    for col in missing_cols:
        core_data[col] = np.nan
    # Reorder columns to match original aggregation order
    core_data = core_data[
        ["subject_id"] + [col for col in agg_dict if col in core_data.columns]]
    core_data = core_data.reset_index()

    # Add Age
    core_data["age"] = trial_as_col_dt(data, core_data, "age", "age")
    # Add Gender
    core_data["gender"] = trial_as_col_dt(data, core_data, "gender", "gender")

    # Add Consent
    consent = data.groupby("subject_id").apply(
        resolve_dict, "consent", "Q0", include_groups=False)
    consent_bool = pd.Series()
    for label, value in consent.items():
        consent_bool[label] = True if "I consent to" in value[0] else False
    core_data["consent"] = core_data["subject_id"].map(consent_bool)

    # Rename Columns
    rename_col_inplace(core_data, "time_elapsed", "completion_time")
    rename_col_inplace(core_data, "adjacency_matrix", "adj_m")
    rename_col_inplace(core_data, "group_name", "var_type")

    # Move Columns (for visualization)
    core_data.insert(0, "subject_id", core_data.pop("subject_id"))
    core_data.insert(4, "age", core_data.pop("age"))
    core_data.insert(5, "gender", core_data.pop("gender"))

    # Get Node order from node file paths
    def extract_ints(str_list):
        """Extract numbers using regex from a of strings."""
        numbers = [int(re.search(r'node(\d+)', path).group(1))
                   for path in str_list]
        return numbers

    core_data["node_order"] = core_data["node_paths"].apply(extract_ints)
    core_data = core_data.drop(columns=["node_paths"])

    # Calculate basic distance matrices
    core_data["spd_m"] = core_data["adj_m"].apply(sdu.get_SPD_matrix)
    core_data["spd_m"] = core_data["spd_m"].apply(arr_to_list)
    if var_type != "unconstrained":
        core_data["eucd_m"] = core_data["node_positions"].apply(
            lambda r: sdu.euclid_dist_matrix(r[0]) if isinstance(r[0][0], list)
            else sdu.euclid_dist_matrix(r)
        )  # pilot 6 is yet without nested list of node positions
        core_data["posw_adj_m"] = core_data["adj_m"] * core_data["eucd_m"]
        core_data["wspd_m"] = core_data["posw_adj_m"].apply(sdu.get_SPD_matrix)

        core_data["eucd_m"] = core_data["eucd_m"].apply(arr_to_list)
        core_data["posw_adj_m"] = core_data["posw_adj_m"].apply(arr_to_list)
        core_data["wspd_m"] = core_data["wspd_m"].apply(arr_to_list)

    # Add Durations
    # ===============
    learn_d = (data.groupby("subject_id")["time_elapsed"].max()
                   .reset_index()
                   .rename(columns={"time_elapsed": "part1_time"})
               )
    test_d = (data.groupby("subject_id")["time_elapsed"].last()
                  .reset_index()
                  .rename(columns={"time_elapsed": "part2_time"})
              )

    # Merge learn and test durations into core_data
    core_data = (core_data
                 .merge(learn_d[["subject_id", "part1_time"]],
                        on="subject_id", how="left")
                 .merge(test_d[["subject_id", "part2_time"]],
                        on="subject_id", how="left")
                 )
    core_data["total_time"] = core_data["part1_time"] \
        + core_data["part2_time"]

    # Convert Variables RTs and and times
    convert_rt_to_seconds(core_data)  # to seconds

    def convert_ms_to_min(dt_series):
        return dt_series / 1000 / 60
    core_data["part1_time"] = convert_ms_to_min(core_data["part1_time"])
    core_data["part2_time"] = convert_ms_to_min(core_data["part2_time"])
    core_data["total_time"] = convert_ms_to_min(core_data["total_time"])

    # Add cheater response (Note: gives error if only 1 subj)
    cheater = data.groupby("subject_id").apply(
        resolve_dict, trial_name="cheater", include_groups=False)
    core_data["cheater"] = core_data["subject_id"].map(cheater)

    # Add start times and time difference (requires columns: age, )
    core_data["start_time_p1"] = core_data.apply(
        partial(combine_date_time_row, list_idx=0), axis=1
    )
    core_data["start_time_p2"] = core_data.apply(
        partial(combine_date_time_row, list_idx=-1), axis=1
    )
    core_data["time_delta_p1_p2"] = (
        core_data["start_time_p2"] - core_data["start_time_p1"]
    ).dt.total_seconds() / 3600.0
    core_data["time_delta_p1_p2"] = core_data["time_delta_p1_p2"].apply(abs)
    core_data["time_delta_p1_p2"] = \
        core_data["time_delta_p1_p2"] - (core_data["part1_time"] / 3600)

    return core_data


def clean_task1_data(data):
    """Clean and preprocess task1 data by extracting, merging, and transforming relevant trial data.

    Steps:
    ------
    1. Filters out data for trials named either "draw_test" or "learn_anim".
    2. Extracts and renames relevant columns from these trials, including trial
       information such as node positions, trial indices, and response times.
    3. Fills missing type information for draw test trials using backward fill
       (`bfill`).
    4. Loads core learning trial information (e.g., group name, number of
       learning passes and blocks) for each participant.
    5. Extracts learning animation trial data and merges it with the core
       participant information.
    6. Extracts draw test trial data and merges it with the existing data.
    7. Excludes trials labeled as "sample" based on the `learnpass_ind` column.
    8. Converts response times (`rt`) from the draw test trials into seconds
       using the `convert_rt_to_seconds` function.
    """
    # Desired columns
    cols_gen = ["subject_id", "trial_name",]
    cols_anim = [
        "node_pos_learnanim", "nodes_clicked_learnanim",
        "trial_ind_learnanim", "type_learnanim", "relation_learnanim",
        "learnpass_ind_learnanim", "rt_learnanim",]
    cols_draw = [
        "type_drawtest", "trial_ind_drawtest", "learnpass_ind_drawtest",
        "nodepos_drawtest", "relation_drawtest", "nb_attempts_drawtest",
        "acc_drawtest", "attempts_drawtest", "attemptout_drawtest",
        "rt_drawtest",]
    cols_desired = cols_gen + cols_anim + cols_draw
    # Keep only columns that exist in the DataFrame
    cols_to_keep = [col for col in cols_desired if col in data.columns]
    learn_trials = data[data["trial_name"].isin(["draw_test", "learn_anim"])][cols_to_keep]

    # Fill the type information in type_drawtest from the antecedent trials and
    # save as general trial type. This is necessary because for some
    # participants I have incorrectly saved the type_learnanim and
    # learnpass_ind_learnanim information. Fortunately it can easily be
    # completed because learnanim and drawtest trials are always paired.
    # Here, I do it for all participants even if I had already found and
    # corrected the arrow.
    learn_trials["type"] = learn_trials["type_drawtest"].bfill()
    learn_trials["learnpass_ind"] = learn_trials["learnpass_ind_drawtest"].bfill()

    # === Load Core Learning Trial Info per Participant ===
    task1_data = (
        data.groupby("subject_id")
        .agg({
            "group_name": "first",
            "nb_learn_passes": "first",
            "nb_learn_blocks": "first",
        })
    )

    # === Extract Learning Animation Trials ===
    learn_trials_anim_data = (
        learn_trials[learn_trials["trial_name"] == "learn_anim"]
        .loc[:, [
            "subject_id", "type",
            "node_pos_learnanim",
            "trial_ind_learnanim",
            "relation_learnanim",
            "learnpass_ind",
        ]]
        .rename(columns={
            "node_pos_learnanim": "nodepos_learnanim",
            "trial_ind_learnanim": "trial_ind",
        })
    )
    # The following columns didn't exist in pilot 6 data yet,
    # therefore add separately
    if "nodes_clicked_learnanim" in learn_trials.columns:
        learn_trials_anim_data["nodes_clicked_learnanim"] = \
            (learn_trials[learn_trials["trial_name"] == "learn_anim"]
                .loc[:, "nodes_clicked_learnanim"])
        learn_trials_anim_data["rt_learnanim"] = \
            (learn_trials[learn_trials["trial_name"] == "learn_anim"]
                .loc[:, "rt_learnanim"])

    task1_data = pd.merge(task1_data, learn_trials_anim_data,
                          on="subject_id", how="left")

    # === Extract Draw Test Trials ===
    learn_trials_draw_data = (
        learn_trials[learn_trials["trial_name"] == "draw_test"]
        .loc[:, [
            "subject_id",
            "trial_name",
            "type",
            "trial_ind_drawtest",
            "learnpass_ind",
            "nodepos_drawtest",
            "relation_drawtest",
            "nb_attempts_drawtest",
            "acc_drawtest",
            "attempts_drawtest",
            "attemptout_drawtest",
        ]]
        .rename(columns={
            "trial_ind_drawtest": "trial_ind",
        })
    )
    # The following column didn't exist in pilot 6 data yet,
    # therefore add separately
    if "rt_drawtest" in learn_trials.columns:
        learn_trials_draw_data["rt_drawtest"] = \
            (learn_trials[learn_trials["trial_name"] == "draw_test"]
                .loc[:, "rt_drawtest"])

    # # === Optional Future Adds ===
    task1_data = pd.merge(
        task1_data, learn_trials_draw_data,
        on=["subject_id", "trial_ind", "learnpass_ind", "type"],
        how="outer").reset_index(drop=True)

    # Eclude sample trials
    task1_data = task1_data[task1_data["learnpass_ind"] != "sample"]
    task1_data = task1_data[task1_data["nodepos_learnanim"].apply(
        lambda x: isinstance(x, list) and len(x) != 3)]
    task1_data = task1_data[task1_data["nodepos_drawtest"].apply(
        lambda x: isinstance(x, list) and len(x) != 3)]

    # Convert Variables
    convert_rt_to_seconds(task1_data)

    return task1_data


def clean_task2_data(data):
    # Learning Trials
    learn_relquest = data[ (data["trial_name"] == "learn_relquest") ]

    task2_data = learn_relquest[[
        "subject_id",
        "trial_name",
        "known_learnrelquest",
        "pair_learnrelquest",
        "trial_ind_learnrelquest",
        "rt",
        "response",
        "correct",
        "trial_index",
        "type_learnrelquest",
    ]]
    task2_data = task2_data.rename(columns={
        "rt": "rt_learnrelquest",
        "response": "response_learnrelquest",
        "correct": "acc_learnrelquest",
        "type_learnrelquest": "type",
    })

    task2_data.reset_index(drop=True, inplace=True)

    # Convert Variables
    convert_rt_to_seconds(task2_data)

    return task2_data


def clean_task3_data(data):
    # Testing Trials
    task3_data = data.groupby("subject_id").agg({
        "group_name": "first",
    })
    task3_data = task3_data.reset_index()

    # Add congruency-test RTs, Acc, Congr
    congr_test_trials = data[data["trial_name"] == "test_congr"]
    congr_task3_data = congr_test_trials[[
        "subject_id",
        "trial_ind_congrtest",
        "pathpair_congrtest",
        "correct",
        "rt",
        "response"
    ]]
    congr_task3_data = congr_task3_data.rename(columns={
        "correct": "acc_congrtest",
        "rt": "rt_congrtest",
    })
    task3_data = pd.merge(task3_data, congr_task3_data)

    # Add conf ratings (Note: gives error if only 1 subj)
    add_conf_ratings(data, task3_data, "congrtest")

    # Add congruency-test strategy (Note: gives error if only 1 subj)
    task3_data["freeeval_congrtest"] = trial_as_col_dt(
        data, task3_data, "freeeval_congrtest", "strategy")

    task3_data.reset_index(drop=True, inplace=True)

    # Convert Variables
    convert_rt_to_seconds(task3_data)

    return task3_data


def clean_task4_data(data):
    """Clean data for task 4."""
    # Add spatial-positioning task test NOREL
    spatialpos_trials = data[data["trial_name"] == "test_spatialpos_norel"]
    task4_data = spatialpos_trials[[
        "subject_id",
        "nodepos_spatialpos_norel",
        "rt",
    ]]
    task4_data = task4_data.rename(columns={
        "rt": "rt_spatialpos_norel",
    })

    # Add spatial-positioning task test REL
    spatialpos_trials_rel = data[data["trial_name"] == "test_spatialpos_rel"]
    spatialpos_rel_data = spatialpos_trials_rel[[
        "subject_id",
        "relations_spatialpos_rel",
        "rt",
    ]]
    spatialpos_rel_data = spatialpos_rel_data.rename(columns={
        "rt": "rt_spatialpos_rel",
    })
    task4_data = pd.merge(task4_data, spatialpos_rel_data)

    # Add conf ratings (Note: gives error if only 1 subj)
    add_conf_ratings(data, task4_data, "spatialpos")
    # Add learnpos strategy (Note: gives error if only 1 subj)
    task4_data["freeeval_spatialpos"] = trial_as_col_dt(
        data, task4_data, "freeeval_spatialpos", "strategy")

    # Clean task 4b responses
    rows = []
    attempts_list = []
    rt_list = []
    for subj in task4_data["subject_id"].unique():
        subj_resp = task4_data[task4_data["subject_id"] == subj]
        rows.append(subj_resp.iloc[-1])
        attempts_list.append(len(subj_resp))
        rt_list.append(subj_resp["rt_spatialpos_rel"].sum())

    cleaned_task4_data = pd.DataFrame(rows)
    cleaned_task4_data["attempts_spatialpos_rel"] = attempts_list
    cleaned_task4_data["rt_spatialpos_rel"] = rt_list
    task4_data = cleaned_task4_data

    task4_data.reset_index(drop=True, inplace=True)

    # Convert Variables
    convert_rt_to_seconds(task4_data)

    return task4_data


if __name__ == "__main__":

    clean_all_data(pilot="batch_1", var_type="rotational")
    clean_all_data(pilot="batch_2", var_type="rotational")

    clean_all_data(pilot="batch_1", var_type="unconstrained")
    clean_all_data(pilot="batch_2", var_type="unconstrained")
