# -*- coding: utf-8 -*-

"""
Step2_GRIDID_assignment.py

Himawari-8 biomass burning optimization

Purpose
-------
Assign each fire detection to a unified 0.02 degree grid.

Input
-----
Step2_LUCC_filtered.csv


Output
------
Step2_GRIDID_assignment/

    FirespotYYYYMM_Step2_GRIDID.csv


Additional outputs
------------------
Step2_GRIDID_assignment_summary.csv

"""


from pathlib import Path
import pandas as pd
import geopandas as gpd
import re
from shapely.geometry import Point



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


grid_file = Path(
    r"E:/Density And Intensity/"
    r"China_Grid_0.02_with_GridID.shp"
)



# =====================================================
# YEAR CONTROL
# =====================================================


start_year = 2016
end_year = 2025



# =====================================================
# COORDINATE
# =====================================================


input_crs = "EPSG:4326"



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
# FILTER YEAR
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
# LOAD GRID
# =====================================================


def load_grid():


    print("="*80)
    print("LOAD GRID")
    print("="*80)


    grid=gpd.read_file(
        grid_file
    )


    print(
        "Grid number:",
        len(grid)
    )


    print(
        grid.columns
    )


    if "GridID" not in grid.columns:

        raise ValueError(
            "GridID field missing"
        )


    grid=grid[
        [
            "GridID",
            "geometry"
        ]
    ]


    if grid.crs != input_crs:

        grid=grid.to_crs(
            input_crs
        )


    return grid




# =====================================================
# PROCESS ONE MONTH
# =====================================================


def process_month(csv_file, grid):


    year,month=parse_year_month(
        csv_file.stem
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

        csv_file,

        encoding="utf-8-sig",

        low_memory=False

    )



    raw=len(df)



    # --------------------------------
    # Point geometry
    # --------------------------------


    gdf=gpd.GeoDataFrame(

        df,

        geometry=gpd.points_from_xy(

            df["Lon"],

            df["Lat"]

        ),

        crs=input_crs

    )



    # --------------------------------
    # Spatial join
    # --------------------------------


    joined=gpd.sjoin(

        gdf,

        grid,

        how="left",

        predicate="within"

    )



    # remove spatial index column

    if "index_right" in joined.columns:

        joined=joined.drop(
            columns=[
                "index_right"
            ]
        )



    assigned=(

        joined["GridID"]

        .notna()

        .sum()

    )


    missing=raw-assigned



    rate=(

        assigned/raw*100

        if raw>0

        else 0

    )



    print(
        "Input:",
        raw
    )

    print(
        "Assigned:",
        assigned
    )

    print(
        "Missing:",
        missing
    )

    print(
        "Rate:",
        round(rate,3),
        "%"
    )



    # --------------------------------
    # Save
    # --------------------------------


    save_dir=(

        output_root

        /
        str(year)

        /
        f"{month_id}_Pre"

        /
        "Step2_GRIDID_assignment"

    )


    save_dir.mkdir(

        parents=True,

        exist_ok=True

    )



    outfile=(

        save_dir

        /

        f"{month_id}_Step2_GRIDID.csv"

    )



    joined.to_csv(

        outfile,

        index=False,

        encoding="utf-8-sig"

    )



    return {


        "Year":year,

        "Month":month,

        "Input_records":raw,

        "GridID_assigned":assigned,

        "GridID_missing":missing,

        "Assignment_rate_%":
        round(rate,3)

    }




# =====================================================
# MAIN
# =====================================================


if __name__=="__main__":


    print("="*80)
    print("SEARCH STEP2 FILES")
    print("="*80)



    files_all=sorted(

        input_root.rglob(

            "*Step2_LUCC_filtered.csv"

        )

    )


    print(
        "All Step2 files:",
        len(files_all)
    )



    files=filter_year(
        files_all
    )


    print(
        "Selected:",
        len(files)
    )



    if len(files)==0:

        raise FileNotFoundError(
            "No Step2 files found"
        )



    grid=load_grid()



    summary=[]



    for f in files:


        result=process_month(

            f,

            grid

        )


        summary.append(
            result
        )



    pd.DataFrame(summary).sort_values(

        [
            "Year",
            "Month"
        ]

    ).to_csv(

        output_root/

        "Step2_GRIDID_assignment_summary.csv",

        index=False,

        encoding="utf-8-sig"

    )



    print("\n")
    print("="*80)
    print("STEP2 GRIDID FINISHED")
    print("="*80)
