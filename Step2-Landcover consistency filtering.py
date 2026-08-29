# -*- coding: utf-8 -*-

"""
Step2 LUCC filtering v3

Himawari-8 biomass burning optimization

Purpose
-------
Remove non-biomass-burning land cover pixels after Step1.

Removed:
0  Invalid boundary
5  Water
6  Ice/Snow
9  Wetland


Retained:
1 Cropland
2 Forest
3 Shrubland
4 Grassland
7 Barren
8 Impervious


Step3 will further analyze:
7 Barren
8 Impervious

"""


from pathlib import Path
import pandas as pd
import re



# =====================================================
# PATH
# =====================================================


input_root = Path(
    r"D:/00 Jiangyizhu/"
    r"H8-Fire_Pre预处理_major revised"
)


output_root = Path(
    r"D:/00 Jiangyizhu/"
    r"H8-Fire_Pre预处理_major revised"
)


output_root.mkdir(
    parents=True,
    exist_ok=True
)



# =====================================================
# YEAR CONTROL
# =====================================================


start_year = 2016
end_year = 2025



# =====================================================
# PARAMETERS
# =====================================================


lucc_column = "LandUse"



remove_lucc = {

    0:"Invalid_boundary",

    5:"Water",

    6:"Ice_Snow",

    9:"Wetland"

}



# =====================================================
# PARSE YYYYMM
# =====================================================


def parse_year_month(name):


    match = re.search(
        r"Firespot(\d{6})",
        name
    )


    if match is None:

        return None,None


    ym = match.group(1)


    return (
        int(ym[:4]),
        int(ym[4:])
    )



# =====================================================
# YEAR FILTER
# =====================================================


def filter_year(files):


    output=[]


    for f in files:


        y,m=parse_year_month(
            f.stem
        )


        if y is None:
            continue


        if start_year <= y <= end_year:

            output.append(f)



    return sorted(output)




# =====================================================
# MONTH CHECK
# =====================================================


def expected_months():


    result=[]


    for y in range(
        start_year,
        end_year+1
    ):

        for m in range(1,13):

            result.append(
                f"{y}{m:02d}"
            )


    return result




def check_months(files):


    records={}


    for f in files:


        y,m=parse_year_month(
            f.stem
        )


        key=f"{y}{m:02d}"


        records.setdefault(
            key,
            []
        ).append(
            str(f)
        )



    expected=set(
        expected_months()
    )


    found=set(
        records.keys()
    )


    missing=sorted(
        expected-found
    )


    duplicate={

        k:v

        for k,v in records.items()

        if len(v)>1

    }



    print("="*80)
    print("MONTH CHECK")
    print("="*80)


    print(
        "Expected:",
        len(expected)
    )

    print(
        "Found:",
        len(found)
    )

    print(
        "Missing:",
        len(missing)
    )

    print(
        "Duplicate:",
        len(duplicate)
    )



    if missing:

        pd.DataFrame(
            {
                "Missing_month":
                missing
            }

        ).to_csv(

            output_root/
            "Step2_missing_months.csv",

            index=False

        )



    if duplicate:


        pd.DataFrame(
            [
                {
                "Month":k,
                "Files":";".join(v)
                }

                for k,v in duplicate.items()

            ]

        ).to_csv(

            output_root/
            "Step2_duplicate_months.csv",

            index=False

        )




# =====================================================
# PROCESS ONE MONTH
# =====================================================


def process_month(file):


    year,month=parse_year_month(
        file.stem
    )


    month_id=f"Firespot{year}{month:02d}"



    print("\n")
    print("="*80)
    print(
        "Processing:",
        month_id
    )
    print("="*80)



    df=pd.read_csv(

        file,

        encoding="utf-8-sig",

        low_memory=False

    )



    if lucc_column not in df.columns:

        raise ValueError(
            f"Missing {lucc_column}"
        )



    # important:
    # avoid string LUCC problem

    df[lucc_column]=pd.to_numeric(

        df[lucc_column],

        errors="coerce"

    )



    before=len(df)



    # -------------------------
    # Before distribution
    # -------------------------


    before_dist=(

        df[lucc_column]

        .value_counts()

        .sort_index()

    )


    before_records=[]


    for k,v in before_dist.items():

        before_records.append(

            {

            "Year":year,

            "Month":month,

            "LandUse":k,

            "Count":v,

            "Stage":
            "Before Step2"

            }

        )



    # -------------------------
    # Count removal
    # -------------------------


    removed={}


    for code,label in remove_lucc.items():

        removed[label]=int(

            (
                df[lucc_column]
                ==
                code

            ).sum()

        )



    # -------------------------
    # Filtering
    # -------------------------


    df_filtered=df[

        ~

        df[lucc_column]

        .isin(

            remove_lucc.keys()

        )

    ].copy()



    after=len(df_filtered)



    total_removed=before-after



    removal_rate=(

        total_removed/

        before*100

        if before>0

        else 0

    )



    # -------------------------
    # After distribution
    # -------------------------


    after_dist=(

        df_filtered[lucc_column]

        .value_counts()

        .sort_index()

    )


    after_records=[]


    for k,v in after_dist.items():

        after_records.append(

            {

            "Year":year,

            "Month":month,

            "LandUse":k,

            "Count":v,

            "Stage":
            "After Step2"

            }

        )




    # -------------------------
    # Save monthly result
    # -------------------------


    save_dir=(

        output_root

        /
        str(year)

        /
        f"{month_id}_Pre"

        /
        "Step2_LUCC_filtering"

    )


    save_dir.mkdir(

        parents=True,

        exist_ok=True

    )



    outfile=(

        save_dir

        /

        f"{month_id}_Step2_LUCC_filtered.csv"

    )



    df_filtered.to_csv(

        outfile,

        index=False,

        encoding="utf-8-sig"

    )



    print(
        "Before:",
        before
    )


    print(
        "Removed:",
        total_removed
    )


    print(
        "After:",
        after
    )


    print(
        "Removal:",
        round(
            removal_rate,
            3
        ),
        "%"
    )



    summary={


        "Year":year,

        "Month":month,


        "Before Step2":
        before,


        "Invalid_boundary removed":
        removed["Invalid_boundary"],


        "Water removed":
        removed["Water"],


        "Ice_Snow removed":
        removed["Ice_Snow"],


        "Wetland removed":
        removed["Wetland"],


        "Total removed":
        total_removed,


        "After Step2":
        after,


        "Removal %":
        round(
            removal_rate,
            3
        )

    }



    return (
        summary,
        before_records,
        after_records
    )





# =====================================================
# MAIN
# =====================================================


if __name__=="__main__":


    print("="*80)
    print("SEARCH STEP1 OUTPUT")
    print("="*80)



    files_all=sorted(

        input_root.rglob(

            "*Step1_confidence_filtered.csv"

        )

    )


    print(
        "All Step1 files:",
        len(files_all)
    )



    files=filter_year(
        files_all
    )


    print(
        "Selected:",
        len(files)
    )



    check_months(files)



    summary=[]

    before=[]

    after=[]



    for f in files:


        s,b,a=process_month(f)


        summary.append(s)

        before.extend(b)

        after.extend(a)



    # summary

    pd.DataFrame(summary).sort_values(

        [
            "Year",
            "Month"

        ]

    ).to_csv(

        output_root/

        "Step2_LUCC_filtering_summary.csv",

        index=False,

        encoding="utf-8-sig"

    )



    pd.DataFrame(before).to_csv(

        output_root/

        "Step2_LUCC_distribution_before.csv",

        index=False,

        encoding="utf-8-sig"

    )



    pd.DataFrame(after).to_csv(

        output_root/

        "Step2_LUCC_distribution_after.csv",

        index=False,

        encoding="utf-8-sig"

    )



    print("\n")
    print("="*80)
    print("STEP2 FINISHED")
    print("="*80)
