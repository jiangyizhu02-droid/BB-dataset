# -*- coding: utf-8 -*-

"""
Step1 Confidence Filtering v3

Himawari-8 fire product optimization

Author: revised workflow

Function:
1. Batch process selected years
2. Automatic YYYYMM recognition
3. Missing month detection
4. Duplicate month detection
5. Reliability distribution
6. Remove low confidence detections
7. Export monthly filtered datasets
8. Generate statistics

"""


from pathlib import Path
import pandas as pd
import re



# =====================================================
# PATH
# =====================================================


input_root = Path(
    r"D:/00 Jiangyizhu"
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
end_year   = 2025



# =====================================================
# PARAMETERS
# =====================================================


confidence_column = "Reliabilit"

low_confidence_value = 1



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


    year=int(
        ym[:4]
    )

    month=int(
        ym[4:6]
    )


    return year,month



# =====================================================
# FILTER YEAR
# =====================================================


def filter_year_range(files):


    selected=[]


    for f in files:

        year,month=parse_year_month(
            f.stem
        )


        if year is None:
            continue


        if (
            start_year
            <= year
            <= end_year
        ):

            selected.append(f)


    return sorted(selected)




# =====================================================
# EXPECTED MONTHS
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




# =====================================================
# FILE CHECK
# =====================================================


def check_files(files):


    print("="*80)
    print("CHECK MONTH COMPLETENESS")
    print("="*80)


    found={}


    for f in files:


        y,m=parse_year_month(
            f.stem
        )


        key=f"{y}{m:02d}"


        if key not in found:

            found[key]=[]


        found[key].append(
            str(f)
        )



    expected=expected_months()


    missing=list(
        set(expected)
        -
        set(found.keys())
    )


    duplicate={

        k:v

        for k,v in found.items()

        if len(v)>1

    }



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


        pd.DataFrame({

            "Missing_month":
            missing

        }).to_csv(

            output_root/
            "missing_months.csv",

            index=False,
            encoding="utf-8-sig"

        )



    if duplicate:


        records=[]


        for k,v in duplicate.items():

            records.append({

                "Month":k,

                "Files":
                ";".join(v)

            })


        pd.DataFrame(
            records
        ).to_csv(

            output_root/
            "duplicate_months.csv",

            index=False,
            encoding="utf-8-sig"

        )





# =====================================================
# PROCESS ONE MONTH
# =====================================================


def process_month(csv_file):


    name=csv_file.stem


    year,month=parse_year_month(
        name
    )


    print("\n")
    print("="*80)
    print(
        "Processing:",
        name
    )
    print("="*80)



    df=pd.read_csv(

        csv_file,

        encoding="utf-8-sig",

        low_memory=False

    )



    total=len(df)



    if confidence_column not in df.columns:

        raise ValueError(
            f"Missing {confidence_column}"
        )



    # -----------------------------
    # Reliability statistics
    # -----------------------------


    rel=df[
        confidence_column
    ].value_counts()



    reliability={

        "Year":year,

        "Month":month,

        "Total":total,

        "Reliability_1":
            rel.get(1,0),

        "Reliability_3":
            rel.get(3,0),

        "Reliability_5":
            rel.get(5,0)

    }




    # -----------------------------
    # Filtering
    # -----------------------------


    removed=(

        df[confidence_column]

        ==
        low_confidence_value

    ).sum()



    df_filtered=df[

        df[confidence_column]

        !=

        low_confidence_value

    ].copy()



    after=len(df_filtered)



    rate=removed/total*100




    # -----------------------------
    # Save
    # -----------------------------


    save_dir=(

        output_root

        /
        str(year)

        /
        f"Firespot{year}{month:02d}_Pre"

        /
        "Step1_confidence_filtering"

    )


    save_dir.mkdir(
        parents=True,
        exist_ok=True
    )



    outfile=(

        save_dir

        /

        f"Firespot{year}{month:02d}_Step1_confidence_filtered.csv"

    )


    df_filtered.to_csv(

        outfile,

        index=False,

        encoding="utf-8-sig"

    )



    print(
        "Raw:",
        total
    )

    print(
        "Removed:",
        removed
    )

    print(
        "After:",
        after
    )

    print(
        "Removal:",
        round(rate,3),
        "%"
    )



    summary={

        "Year":year,

        "Month":month,

        "Raw":total,

        "Low confidence removed":
            removed,

        "After filtering":
            after,

        "Removal %":
            round(rate,3)

    }



    return summary,reliability




# =====================================================
# MAIN
# =====================================================


if __name__=="__main__":


    print("="*80)
    print("SEARCH FILES")
    print("="*80)



    all_files=sorted(

        input_root.rglob(

            "Firespot*_LUCC.csv"

        )

    )



    print(
        "All files:",
        len(all_files)
    )



    files=filter_year_range(
        all_files
    )



    print(
        "Selected files:",
        len(files)
    )


    print(
        f"Years: {start_year}-{end_year}"
    )



    if len(files)==0:

        raise FileNotFoundError(
            "No selected year files"
        )



    check_files(files)



    summary=[]

    reliability=[]



    for f in files:


        s,r=process_month(f)

        summary.append(s)

        reliability.append(r)




    # summary


    pd.DataFrame(
        summary
    ).sort_values(

        [
            "Year",
            "Month"
        ]

    ).to_csv(

        output_root/
        "Step1_confidence_filtering_summary.csv",

        index=False,

        encoding="utf-8-sig"

    )



    pd.DataFrame(
        reliability
    ).sort_values(

        [
            "Year",
            "Month"
        ]

    ).to_csv(

        output_root/
        "Step1_Reliability_distribution.csv",

        index=False,

        encoding="utf-8-sig"

    )



    print("\nFINISHED")
