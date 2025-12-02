DROP TABLE IF EXISTS combined_data;
--Tables
CREATE TABLE combined_data AS
    -- Los Angeles
    SELECT
        "Date",
        "Time",
        "Location" as location,
        nibrs_code,
        "Crm Cd Desc" as description,
        CLOSEST_STATION,
        CLOSEST_STATION_OBJECTID,
        DISTANCE_METERS
    FROM read_csv_auto('los_angeles_clean.csv')
    WHERE YEAR("Date Rptd"::DATE) = 2020  -- Filter for LA

UNION ALL

    -- Chicago
    SELECT
        "Date",
        "Time",
        "Block" as location,
        nibrs_code,
        Description as description,
        CLOSEST_STATION_NAME as CLOSEST_STATION,
        CLOSEST_STATION_OBJECTID,
        DISTANCE_METERS
    FROM read_csv_auto('Chicago_clean.csv')
    WHERE YEAR("Date"::DATE) = 2020       -- Filter for Chicago

UNION ALL

    -- Philadelphia
    SELECT
        "Date",
        "Time",
        location_block as location,
        nibrs_code,
        text_general_code as description,
        CLOSEST_STATION_NAME as CLOSEST_STATION,
        CLOSEST_STATION_OBJECTID,
        DISTANCE_METERS
    FROM read_csv_auto('philly_clean.csv')
    WHERE YEAR(dispatch_date_time::DATE) = 2020; -- Filter for Philly
