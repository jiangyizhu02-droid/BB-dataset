# -*- coding: utf-8 -*-

"""
Step3_detection_filtering_v4.py

Purpose
-------
Convert Step3 anomaly grid-day results into real fire detection removal.

Improvements:
1. Automatically recognize fields with trailing "_"
   Example:
       Year / Year_
       Month / Month_
       Day / Day_
       GridID / GridID_

2. Avoid GridID type mismatch

3. Preserve Step2 original files

4. Save:
   - anomaly union
   - retained detections
   - removed detections
   - removal statistics


"""

from pathlib import Path
import pandas as pd
import re


root = Path(
    r"D:/00 Jiangyizhu/H8-Fire_Pre预处理_major revised"
)


single_file = (
    root /
    "Step3_single_day_results" /
    "Step3_P95_anomaly_grid_day.csv"
)

multi_file = (
    root /
    "Step3_multi_day_results_v4" /
    "Step3_multi_day_anomaly_records_v4.csv"
)


output_root = (
    root /
    "Step3_detection_filtered_v4"
)

output_root.mkdir(
    parents=True,
    exist_ok=True
)


start_year = 2016
end_year = 2025



def clean_columns(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df



def find_column(df, candidates):

    cols = df.columns.tolist()

    # exact match
    for c in candidates:
        if c in cols:
            return c

    # ignore trailing underscore
    for col in cols:

        col_clean = col.rstrip("_")

        for c in candidates:

            if col_clean.lower() == c.lower():
                return col


    raise ValueError(
        f"Cannot find column from {candidates}. "
        f"Available columns: {cols}"
    )



def parse_year_month(name):

    m = re.search(
        r"Firespot(\d{6})",
        name
    )

    if m is None:
        return None, None

    ym = m.group(1)

    return (
        int(ym[:4]),
        int(ym[4:])
    )



def load_anomaly():


    print("="*80)
    print("LOAD ANOMALY")
    print("="*80)


    single = clean_columns(
        pd.read_csv(
            single_file,
            low_memory=False
        )
    )


    multi = clean_columns(
        pd.read_csv(
            multi_file,
            low_memory=False
        )
    )


    single_key = single[
        [
            "GridID",
            "Date_ID"
        ]
    ].copy()


    multi_key = multi[
        [
            "GridID",
            "Date_ID"
        ]
    ].copy()


    for df in [single_key, multi_key]:

        df["GridID"] = (
            pd.to_numeric(
                df["GridID"],
                errors="coerce"
            )
            .astype("Int64")
            .astype(str)
        )


    union = pd.concat(
        [
            single_key,
            multi_key
        ],
        ignore_index=True
    )


    union = union.drop_duplicates(
        [
            "GridID",
            "Date_ID"
        ]
    )


    save_dir = (
        output_root /
        "anomaly_union"
    )

    save_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    union.to_csv(
        save_dir /
        "Step3_anomaly_union_grid_day.csv",
        index=False,
        encoding="utf-8-sig"
    )


    print(
        "Anomaly grid-day:",
        len(union)
    )


    return union



def find_step2():

    files=[]

    for f in root.rglob(
        "*Step2_GRIDID.csv"
    ):

        y,m = parse_year_month(
            f.stem
        )

        if y is not None:

            if start_year <= y <= end_year:

                files.append(f)


    return sorted(files)



def process(file, anomaly):


    y,m = parse_year_month(
        file.stem
    )


    print(
        f"Processing {y}-{m:02d}"
    )


    df = clean_columns(
        pd.read_csv(
            file,
            low_memory=False
        )
    )


    before = len(df)


    # GridID auto detection
    grid_col = find_column(
        df,
        [
            "GridID",
            "gridid",
            "GRIDID"
        ]
    )


    df["GridID"] = (
        pd.to_numeric(
            df[grid_col],
            errors="coerce"
        )
        .astype("Int64")
        .astype(str)
    )


    # Date_ID generation
    if "Date_ID" not in df.columns:


        year_col = find_column(
            df,
            [
                "Year",
                "year"
            ]
        )


        month_col = find_column(
            df,
            [
                "Month",
                "month"
            ]
        )


        day_col = find_column(
            df,
            [
                "Day",
                "day"
            ]
        )


        df["Date_ID"] = pd.to_datetime(
            {
                "year":
                pd.to_numeric(
                    df[year_col],
                    errors="coerce"
                ),

                "month":
                pd.to_numeric(
                    df[month_col],
                    errors="coerce"
                ),

                "day":
                pd.to_numeric(
                    df[day_col],
                    errors="coerce"
                )
            },
            errors="coerce"
        ).dt.strftime(
            "%Y-%m-%d"
        )


    merged = df.merge(
        anomaly,
        on=[
            "GridID",
            "Date_ID"
        ],
        how="left",
        indicator=True
    )


    removed = merged[
        merged["_merge"]=="both"
    ].drop(
        columns=["_merge"]
    )


    remain = merged[
        merged["_merge"]!="both"
    ].drop(
        columns=["_merge"]
    )


    out1 = (
        output_root /
        "detection_filtered" /
        str(y)
    )

    out1.mkdir(
        parents=True,
        exist_ok=True
    )


    remain.to_csv(
        out1 /
        f"Firespot{y}{m:02d}_Step3_filtered.csv",
        index=False,
        encoding="utf-8-sig"
    )


    out2 = (
        output_root /
        "detection_removed" /
        str(y)
    )

    out2.mkdir(
        parents=True,
        exist_ok=True
    )


    removed.to_csv(
        out2 /
        f"Firespot{y}{m:02d}_Step3_removed.csv",
        index=False,
        encoding="utf-8-sig"
    )


    return {

        "Year":y,

        "Month":m,

        "Before":before,

        "Removed":len(removed),

        "Remaining":len(remain),

        "Removal_%":
        round(
            len(removed)/before*100,
            3
        )

    }



if __name__ == "__main__":


    anomaly = load_anomaly()


    files = find_step2()


    print(
        "Step2 files:",
        len(files)
    )


    results=[]


    for f in files:

        results.append(
            process(
                f,
                anomaly
            )
        )


    stat = pd.DataFrame(results)


    stat = stat.sort_values(
        [
            "Year",
            "Month"
        ]
    )


    stat.to_csv(
        output_root /
        "Step3_detection_removal_statistics.csv",
        index=False,
        encoding="utf-8-sig"
    )


    print("\nFINAL SUMMARY")

    print(stat)


    print(
        "Before:",
        stat["Before"].sum()
    )

    print(
        "Removed:",
        stat["Removed"].sum()
    )

    print(
        "Remaining:",
        stat["Remaining"].sum()
    )

    print("FINISHED")
