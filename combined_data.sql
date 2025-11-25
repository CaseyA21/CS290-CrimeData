DROP TABLE IF EXISTS combined_data;
--Tables
CREATE TABLE combined_data AS
    -- Los Angeles
    SELECT
        "Date Rptd"::DATE as date_occ,
        "Location" as location,
        "Crm Cd" as nibrs_code,
        "Crm Cd Desc" as description,
        LAT,
        LON
    FROM read_csv_auto('los_angeles_clean.csv')
    WHERE YEAR("Date Rptd"::DATE) = 2020  -- Filter for LA

UNION ALL

    -- Chicago
    SELECT
        "Date"::DATE as date_occ,
        "Block" as location,
        nibrs_code,
        Description as description,
        latitude as LAT,
        longitude as LON,
    FROM read_csv_auto('chicago_clean.csv')
    WHERE YEAR("Date"::DATE) = 2020       -- Filter for Chicago

UNION ALL

    -- Philadelphia
    SELECT
        dispatch_date_time::DATE as date_occ,
        location_block as location,
        nibrs_code,
        text_general_code as description,
        lat as LAT,
        lng as LON,
    FROM read_csv_auto('philly_clean.csv')
    WHERE YEAR(dispatch_date_time::DATE) = 2020; -- Filter for Philly
