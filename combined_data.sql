DROP TABLE combined_data;

CREATE TABLE combined_data AS
    SELECT
        "Date Rptd" as date_occ,
        "Location" as location,
        "Crm Cd" as nibrs_code,
        "Crm Cd Desc" as description,
        LAT,
        LON
    FROM read_csv_auto('los_angeles_clean.csv')

UNION ALL

SELECT
    "Date" as date_occ,
    "Block" as location,
    nibrs_code,
    Description as description,
    latitude as LAT,
    longitude as LON,
FROM read_csv_auto('chicago_clean.csv')

UNION ALL

SELECT
    dispatch_date_time as date_occ,
    location_block as location,
    nibrs_code,
    text_general_code as description,
    lat as LAT,
    lng as LON,
FROM read_csv_auto('philly_clean.csv')