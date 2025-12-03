import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from pyproj import Transformer
import duckdb

# ============================================================================
# PART 1: DATA LOADING AND NIBRS CODE MAPPING
# ============================================================================

print("Loading crime data...")
philly = pd.read_csv("incidents_part1_part2.csv")
chicago = pd.read_csv("Crimes_-_2001_to_Present.csv")
los_angeles = pd.read_csv("Crime_Data_from_2020_to_Present.csv")

print("Loading police station data...")
philly_police = pd.read_csv('Philly_Police_Stations.csv')
chicago_police = pd.read_csv('Chicago_Police_Stations_20251111.csv')
los_angeles_police = pd.read_csv('LAPD_Police_Stations_-3946316159051949741.csv')

# ----------------------------------------------------------------------------
# PHILADELPHIA PROCESSING
# ----------------------------------------------------------------------------
print("\nProcessing Philadelphia data...")

# Mapping Philly descriptions to NIBRS 2011 codes
philly_nibrs_crosswalk = {
    'Homicide - Criminal': '09A',
    'Homicide - Justifiable': '09C',
    'Rape': '11A',
    'Robbery No Firearm': '120',
    'Robbery Firearm': '120',
    'Aggravated Assault Firearm': '13A',
    'Aggravated Assault No Firearm': '13A',
    'Burglary Non-Residential': '220',
    'Burglary Residential': '220',
    'Thefts': '23H',
    'Theft from Vehicle': '23F',
    'Motor Vehicle Theft': '240',
    'Other Assaults': '13B',
    'Arson': '200',
    'Forgery and Counterfeiting': '250',
    'Fraud': '26A',
    'Embezzlement': '270',
    'Receiving Stolen Property': '280',
    'Vandalism/Criminal Mischief': '290',
    'Weapon Violations': '520',
    'Prostitution and Commercialized Vice': '40A',
    'Other Sex Offenses (Not Commercialized)': '36B',
    'Narcotic / Drug Law Violations': '35A',
    'Gambling Violations': '39A',
    'Offenses Against Family and Children': '90F',
    'DRIVING UNDER THE INFLUENCE': '90D',
    'Liquor Law Violations': '90G',
    'Public Drunkenness': '90E',
    'Disorderly Conduct': '90C',
    'Vagrancy/Loitering': '90B',
}

philly['nibrs_code'] = philly['text_general_code'].map(philly_nibrs_crosswalk).fillna('90Z')
philly['text_general_code'] = philly.apply(
    lambda row: 'Other Offenses' if row['nibrs_code'] == '90Z' and row['text_general_code'] not in philly_nibrs_crosswalk else row['text_general_code'],
    axis=1
)

# Creates Time and Date columns
philly['dispatch_date_time'] = pd.to_datetime(philly['dispatch_date_time'], utc=True)
philly['Time'] = philly['dispatch_date_time'].dt.time
philly['Date'] = philly['dispatch_date_time'].dt.date

# ----------------------------------------------------------------------------
# CHICAGO PROCESSING
# ----------------------------------------------------------------------------
print("Processing Chicago data...")

chicago['IUCR'] = chicago['IUCR'].astype(str).str.strip()

# Mapping Chicago IUCR codes to NIBRS 2011 codes
chicago_nibrs_crosswalk = {
    # Homicide Offenses
    '0110': '09A', '0130': '09A',
    '0141': '09B', '0142': '09B',
    # Criminal Sexual Assault
    '0261': '11A', '0262': '11A', '0263': '11A', '0264': '11A', '0265': '11A',
    '0266': '11A', '0271': '11A', '0272': '11A', '0273': '11A', '0274': '11A',
    '0275': '11A', '0281': '11A', '0291': '11A',
    # Robbery
    '0312': '120', '0313': '120', '031A': '120', '031B': '120', '0320': '120',
    '0325': '120', '0326': '120', '0330': '120', '0331': '120', '0334': '120',
    '0337': '120', '033A': '120', '033B': '120', '0340': '120',
    # Battery - Aggravated Assault
    '041A': '13A', '041B': '13A', '0420': '13A', '0430': '13A', '0440': '13A',
    '0450': '13A', '0451': '13A', '0452': '13A', '0453': '13A', '0454': '13A',
    '0460': '13A', '0461': '13A', '0462': '13A', '0475': '13A', '0479': '13A',
    '0480': '13A', '0481': '13A', '0482': '13A', '0483': '13A', '0484': '13A',
    '0485': '13A', '0486': '13A', '0487': '13A', '0488': '13A', '0489': '13A',
    '0495': '13A', '0496': '13A', '0497': '13A', '0498': '13A', '0499': '13A',
    # Assault - Aggravated Assault
    '051A': '13A', '051B': '13A', '0520': '13A', '0530': '13A', '0545': '13A',
    '0550': '13A', '0551': '13A', '0552': '13A', '0553': '13A', '0554': '13A',
    '0555': '13A', '0556': '13A', '0557': '13A', '0558': '13A', '0560': '13A',
    # Stalking - Intimidation
    '0580': '13C', '0581': '13C', '0583': '13C', '0584': '13C',
    # Burglary
    '0610': '220', '0620': '220', '0630': '220', '0650': '220', '0760': '220',
    # Theft
    '0710': '23F',
    '0810': '23H', '0820': '23H', '0830': '23C', '0840': '23H', '0841': '23H',
    '0842': '23H', '0843': '23H', '0850': '23D', '0860': '23H', '0865': '23E',
    '0870': '23A', '0880': '23B', '0890': '23D', '0895': '23E',
    # Motor Vehicle Theft
    '0910': '240', '0915': '240', '0917': '240', '0918': '240', '0920': '240',
    '0925': '240', '0927': '240', '0928': '240', '0930': '240', '0935': '240',
    '0937': '240', '0938': '240',
    # Arson
    '1010': '200', '1020': '200', '1025': '200', '1030': '200', '1035': '200',
    '1090': '200',
    # Human Trafficking
    '1050': '40B', '1055': '40B',
    # Deceptive Practice
    '1101': '26A', '1102': '26A', '1110': '26A', '1120': '250', '1121': '250',
    '1122': '250', '1130': '26A', '1135': '26A', '1140': '26A', '1150': '26A',
    '1151': '26A', '1152': '26A', '1153': '26A', '1154': '26A', '1155': '26A',
    '1156': '26A', '1160': '26A', '1170': '26A', '1185': '26A', '1187': '26A',
    '1192': '26A', '1195': '26A', '1197': '26A', '1199': '26A', '1200': '26A',
    '1205': '26A', '1206': '26A', '1210': '26A', '1220': '26A', '1230': '26A',
    '1235': '26A', '1240': '26A', '1241': '26A', '1242': '26A', '1245': '26A',
    '1255': '26A', '1260': '26A', '1261': '26A', '1262': '26A', '1263': '26A',
    # Criminal Damage
    '1265': '290', '1305': '290', '1310': '290', '1320': '290', '1330': '290',
    '1335': '290', '1340': '290', '1345': '290', '1350': '290', '1360': '290',
    '1365': '290', '1370': '290', '1375': '290',
    # Weapons Violations
    '141A': '520', '141B': '520', '141C': '520', '142A': '520', '142B': '520',
    '1435': '520', '143A': '520', '143B': '520', '143C': '520', '1440': '520',
    '1450': '520', '1460': '520', '1476': '520', '1477': '520', '1478': '520',
    '1479': '520', '1480': '520', '2900': '520',
    # Sex Offenses and Prostitution
    '1504': '11D', '1505': '40A', '1506': '40A', '1507': '40A', '1510': '40A',
    '1511': '40A', '1512': '40A', '1513': '40A', '1515': '40A', '1518': '370',
    '1519': '90Z', '1520': '40A', '1521': '40A', '1525': '40A', '1526': '40A',
    '1530': '40A', '1531': '40A', '1535': '370', '1536': '370', '1537': '90Z',
    '1540': '370', '1541': '370', '1542': '370', '1544': '11D', '1549': '40A',
    '1562': '36B', '1563': '36B', '1564': '36B', '1565': '36B', '1566': '36B',
    '1570': '11D', '1572': '11D', '1573': '11D', '1574': '11D', '1576': '11D',
    '1577': '11D', '1578': '11D', '1580': '36B', '1581': '36B', '1582': '36A',
    '1585': '11D', '1590': '36B', '1599': '11D',
    # Gambling
    '1610': '39A', '1611': '39A', '1620': '39A', '1621': '39A', '1622': '39A',
    '1624': '39A', '1625': '39A', '1626': '39A', '1627': '39A', '1630': '39A',
    '1631': '39A', '1633': '39A', '1640': '39A', '1650': '39A', '1651': '39A',
    '1661': '39A', '1670': '39A', '1680': '39A', '1681': '39A', '1682': '90Z',
    '1697': '39A',
    # Offenses Involving Children
    '1710': '90F', '1715': '90F', '1720': '90F', '1725': '90F', '1726': '90F',
    '1750': '90F', '1751': '90F', '1752': '90F', '1753': '90F', '1754': '90F',
    '1755': '90F', '1780': '90F', '1790': '90F', '1791': '90F',
    # Kidnapping
    '1792': '100', '4210': '100', '4220': '100', '4230': '100', '4240': '100',
    '4255': '100',
    # Narcotics
    '1811': '35A', '1812': '35A', '1821': '35A', '1822': '35A', '1840': '35A',
    '1850': '35A', '1860': '35A', '1900': '35A', '2010': '35A', '2011': '35A',
    '2012': '35A', '2013': '35A', '2014': '35A', '2015': '35A', '2016': '35A',
    '2017': '35A', '2018': '35A', '2019': '35A', '2020': '35A', '2021': '35A',
    '2022': '35A', '2023': '35A', '2024': '35A', '2025': '35A', '2026': '35A',
    '2027': '35A', '2028': '35A', '2029': '35A', '2030': '35A', '2031': '35A',
    '2032': '35A', '2033': '35A', '2034': '35A', '2040': '35A', '2050': '35A',
    '2060': '35A', '2070': '35A', '2080': '35A', '2090': '35A', '2091': '35A',
    '2092': '35A', '2093': '35A', '2094': '35A', '2095': '35A', '2110': '35A',
    '2111': '35A', '2120': '35A', '2160': '35A', '2170': '35A',
    # Liquor Law Violations
    '2210': '90G', '2220': '90G', '2230': '90G', '2240': '90G', '2250': '90G',
    '2251': '90G',
    # Public Peace Violations
    '0470': '90C', '2840': '90C', '2850': '90C', '2851': '90C', '2860': '90C',
    '2870': '90C', '2890': '90C', '2895': '90C', '2896': '90C', '3000': '90C',
    '3100': '90C', '3200': '90C', '3300': '90C', '3400': '90C',
    # Intimidation
    '3960': '13C', '3961': '13C', '3966': '13C', '3970': '13C', '3975': '13C',
    '3980': '13C',
    # Domestic Violence
    '9901': '90F',
}

chicago['nibrs_code'] = chicago['IUCR'].map(chicago_nibrs_crosswalk).fillna('90Z')
chicago['Description'] = chicago.apply(
    lambda row: 'Other Offenses' if row['nibrs_code'] == '90Z' and row['IUCR'] not in chicago_nibrs_crosswalk else row['Description'],
    axis=1
)

# Creates Time and Date columns
chicago['Date'] = pd.to_datetime(chicago['Date'], format='mixed', errors='coerce')
chicago['Time'] = chicago['Date'].dt.time
chicago['Date'] = chicago['Date'].dt.date

# ----------------------------------------------------------------------------
# LOS ANGELES PROCESSING
# ----------------------------------------------------------------------------
print("Processing Los Angeles data...")

los_angeles['Crm Cd'] = los_angeles['Crm Cd'].astype(str).str.strip()

# Mapping LA Crime Codes to NIBRS 2011 codes
la_nibrs_crosswalk = {
    '110': '09A', '113': '09B',
    '121': '11A', '122': '11A', '760': '11D', '815': '11C', '820': '11B',
    '821': '11B', '860': '11D',
    '210': '120', '220': '120',
    '230': '13A', '231': '13A', '235': '13A', '236': '13A', '250': '13A',
    '251': '13A', '622': '13B', '623': '13B', '624': '13B', '625': '13B',
    '626': '13B', '627': '13B', '647': '13B', '237': '90F',
    '310': '220', '320': '220', '330': '220', '410': '220',
    '331': '23F', '420': '23F', '421': '23F', '341': '23H', '343': '23C',
    '345': '23H', '347': '23H', '349': '23H', '350': '23H', '351': '23B',
    '352': '23A', '353': '23H', '354': '23H', '440': '23H', '441': '23H',
    '442': '23C', '443': '23C', '444': '23H', '445': '23H', '446': '23H',
    '450': '23H', '451': '23B', '452': '23A', '453': '23H', '470': '23H',
    '471': '23H', '473': '23E', '474': '23E', '475': '23E', '480': '23H',
    '485': '23H', '487': '23H',
    '510': '240', '520': '240', '522': '240', '433': '240',
    '648': '200',
    '940': '210',
    '649': '250', '651': '250', '652': '250', '660': '250',
    '653': '26B', '654': '26B', '661': '26C', '662': '26A', '664': '26A',
    '666': '26A', '950': '26A', '951': '26A',
    '668': '270', '670': '270',
    '740': '290', '745': '290',
    '753': '520', '755': '520', '756': '520', '761': '520', '904': '520',
    '906': '520', '931': '520',
    '805': '40A', '806': '40B', '810': '40A',
    '812': '36B', '813': '36B', '814': '370', '822': '40B', '830': '36A',
    '840': '36B', '845': '90Z', '850': '370', '762': '370', '956': '370',
    '910': '100', '920': '100', '921': '100', '922': '100',
    '942': '510',
    '763': '13C', '928': '13C', '930': '13C',
    '865': '35A',
    '870': '90F', '954': '90F',
    '880': '90C', '882': '90C', '884': '90C', '886': '90C',
    '888': '90J',
}

los_angeles['nibrs_code'] = los_angeles['Crm Cd'].map(la_nibrs_crosswalk).fillna('90Z')
los_angeles['Crm Cd Desc'] = los_angeles.apply(
    lambda row: 'Other Offenses' if row['nibrs_code'] == '90Z' and row['Crm Cd'] not in la_nibrs_crosswalk else row['Crm Cd Desc'],
    axis=1
)

# Creates Time and Date columns
los_angeles['TIME OCC'] = los_angeles['TIME OCC'].astype(str).str.zfill(4)
los_angeles['TIME OCC'] = (
    los_angeles['TIME OCC'].str.slice(0, 2) + ':' +
    los_angeles['TIME OCC'].str.slice(2, 4) + ':00'
)
los_angeles['DATE OCC'] = pd.to_datetime(
    los_angeles['DATE OCC'].str.split().str[0],
    format='%m/%d/%Y'
)
los_angeles['Time'] = los_angeles['TIME OCC']
los_angeles['Date'] = los_angeles['DATE OCC']

# ============================================================================
# PART 2: CLOSEST POLICE STATION CALCULATIONS
# ============================================================================

DISTANCE_CRS = "EPSG:3857"

# ----------------------------------------------------------------------------
# PHILADELPHIA - Closest Station
# ----------------------------------------------------------------------------
print("\nCalculating closest stations for Philadelphia...")

philly_police["LATITUDE"] = philly_police["Y"]
philly_police["LONGITUDE"] = philly_police["X"]

# Clean crime data
philly = philly.dropna(subset=['lat', 'lng']).copy()

# Crime GeoDataFrame
philly['geometry'] = [Point(xy) for xy in zip(philly['lng'], philly['lat'])]
crimes_gdf = gpd.GeoDataFrame(philly, geometry='geometry', crs="EPSG:4326")
crimes_gdf = crimes_gdf.to_crs(DISTANCE_CRS)

# Station GeoDataFrame (PA State Plane South - feet)
philly_police['geometry'] = [Point(xy) for xy in zip(philly_police['LONGITUDE'], philly_police['LATITUDE'])]
stations_gdf = gpd.GeoDataFrame(philly_police, geometry='geometry', crs="EPSG:2272")
stations_gdf = stations_gdf.to_crs(DISTANCE_CRS)

# Prepare coordinates
crime_coords = np.array([(geom.x, geom.y) for geom in crimes_gdf.geometry])
station_coords = np.array([(geom.x, geom.y) for geom in stations_gdf.geometry])

# Extract identifiers
station_names = stations_gdf['LOCATION'].values
station_object_ids = stations_gdf['DISTRICT_N'].values

# KDTree search
tree = cKDTree(station_coords)
distances, indices = tree.query(crime_coords)

# Save results
philly['CLOSEST_STATION_NAME'] = station_names[indices]
philly['CLOSEST_STATION_OBJECTID'] = station_object_ids[indices]
philly['DISTANCE_METERS'] = distances

# ----------------------------------------------------------------------------
# CHICAGO - Closest Station
# ----------------------------------------------------------------------------
print("Calculating closest stations for Chicago...")

# Clean crime data
initial_count = len(chicago)
chicago = chicago.dropna(subset=['Latitude', 'Longitude']).copy()
print(f"Chicago: Dropped {initial_count - len(chicago)} records with missing coordinates.")

# Crime GeoDataFrame
chicago['geometry'] = [Point(xy) for xy in zip(chicago['Longitude'], chicago['Latitude'])]
crimes_gdf = gpd.GeoDataFrame(chicago, geometry='geometry', crs="EPSG:4326").to_crs(DISTANCE_CRS)

# Clean police data
initial_police = len(chicago_police)
chicago_police = chicago_police.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
print(f"Chicago Police: Dropped {initial_police - len(chicago_police)} records with missing coordinates.")

# Station GeoDataFrame
chicago_police['geometry'] = [Point(xy) for xy in zip(chicago_police['LONGITUDE'], chicago_police['LATITUDE'])]
stations_gdf = gpd.GeoDataFrame(chicago_police, geometry='geometry', crs="EPSG:4326").to_crs(DISTANCE_CRS)

# Extract coordinates
crime_coords = np.array(crimes_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist())
station_coords = np.array(stations_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist())

# Extract identifiers
station_names = stations_gdf['DISTRICT NAME'].values
station_object_ids = stations_gdf['DISTRICT'].values

# KDTree search
tree = cKDTree(station_coords)
distances, indices = tree.query(crime_coords)

# Save results
results = pd.DataFrame({
    'CLOSEST_STATION_NAME': station_names[indices],
    'CLOSEST_STATION_OBJECTID': station_object_ids[indices],
    'DISTANCE_METERS': distances
}, index=crimes_gdf.index)

chicago = chicago.join(results)

# ----------------------------------------------------------------------------
# LOS ANGELES - Closest Station
# ----------------------------------------------------------------------------
print("Calculating closest stations for Los Angeles...")

# Transform LA police station coordinates
transformer = Transformer.from_crs('EPSG:2229', 'EPSG:4326', always_xy=True)
los_angeles_police['LONGITUDE'], los_angeles_police['LATITUDE'] = transformer.transform(
    los_angeles_police['x'].values,
    los_angeles_police['y'].values
)

# Crime GeoDataFrame
los_angeles['geometry'] = [Point(xy) for xy in zip(los_angeles['LON'], los_angeles['LAT'])]
crimes_gdf = gpd.GeoDataFrame(los_angeles, geometry='geometry', crs="EPSG:4326")
crimes_gdf = crimes_gdf.to_crs("EPSG:3857")

# Station GeoDataFrame
los_angeles_police['geometry'] = [Point(xy) for xy in zip(los_angeles_police['LONGITUDE'], los_angeles_police['LATITUDE'])]
stations_gdf = gpd.GeoDataFrame(los_angeles_police, geometry='geometry', crs="EPSG:4326")
stations_gdf = stations_gdf.to_crs(crimes_gdf.crs)

# Extract coordinates
crime_coords = np.array(crimes_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist())
station_coords = np.array(stations_gdf.geometry.apply(lambda geom: (geom.x, geom.y)).tolist())

# Extract identifiers
station_names = stations_gdf['DIVISION'].values
station_object_ids = stations_gdf['OBJECTID'].values

# KDTree search
tree = cKDTree(station_coords)
distances, indices = tree.query(crime_coords)

# Save results
los_angeles['CLOSEST_STATION'] = station_names[indices]
los_angeles['CLOSEST_STATION_OBJECTID'] = station_object_ids[indices]
los_angeles['DISTANCE_METERS'] = distances
los_angeles.drop('geometry', axis=1, inplace=True)

# ============================================================================
# PART 3: ADD CITY, MONTH, DAY, AND IS_WEEKEND COLUMNS
# ============================================================================

print("\nAdding city, month, day, and is_weekend columns...")

# Convert date columns to proper datetime format
los_angeles['Date Rptd'] = pd.to_datetime(los_angeles['Date Rptd'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
chicago['Date'] = pd.to_datetime(chicago['Date'], format='mixed', errors='coerce')
philly['dispatch_date_time'] = pd.to_datetime(philly['dispatch_date_time'], utc=True, errors='coerce')

# Los Angeles - Add new columns
los_angeles['city'] = 'Los Angeles'
los_angeles['month'] = pd.to_datetime(los_angeles['Date']).dt.month
los_angeles['day'] = pd.to_datetime(los_angeles['Date']).dt.day
los_angeles['is_weekend'] = pd.to_datetime(los_angeles['Date']).dt.dayofweek.isin([5, 6]).astype(int)

# Chicago - Add new columns
chicago['city'] = 'Chicago'
chicago['month'] = pd.to_datetime(chicago['Date']).dt.month
chicago['day'] = pd.to_datetime(chicago['Date']).dt.day
chicago['is_weekend'] = pd.to_datetime(chicago['Date']).dt.dayofweek.isin([5, 6]).astype(int)

# Philadelphia - Add new columns
philly['city'] = 'Philadelphia'
philly['month'] = pd.to_datetime(philly['Date']).dt.month
philly['day'] = pd.to_datetime(philly['Date']).dt.day
philly['is_weekend'] = pd.to_datetime(philly['Date']).dt.dayofweek.isin([5, 6]).astype(int)

# Clean data - remove rows with ANY null values in key columns (using actual DataFrame column names)
key_columns_la = ['city', 'Date', 'Time', 'month', 'day', 'is_weekend', 'nibrs_code', 'Crm Cd Desc', 'CLOSEST_STATION', 'CLOSEST_STATION_OBJECTID', 'DISTANCE_METERS']
key_columns_chicago = ['city', 'Date', 'Time', 'month', 'day', 'is_weekend', 'Block', 'nibrs_code', 'Description', 'CLOSEST_STATION_NAME', 'CLOSEST_STATION_OBJECTID', 'DISTANCE_METERS']
key_columns_philly = ['city', 'Date', 'Time', 'month', 'day', 'is_weekend', 'location_block', 'nibrs_code', 'text_general_code', 'CLOSEST_STATION_NAME', 'CLOSEST_STATION_OBJECTID', 'DISTANCE_METERS']

print(f"Los Angeles before cleaning: {len(los_angeles)} rows")
los_angeles = los_angeles.dropna(subset=key_columns_la)
print(f"Los Angeles after cleaning: {len(los_angeles)} rows")

print(f"Chicago before cleaning: {len(chicago)} rows")
chicago = chicago.dropna(subset=key_columns_chicago)
print(f"Chicago after cleaning: {len(chicago)} rows")

print(f"Philadelphia before cleaning: {len(philly)} rows")
philly = philly.dropna(subset=key_columns_philly)
print(f"Philadelphia after cleaning: {len(philly)} rows")

# ============================================================================
# PART 4: DUCKDB COMBINATION
# ============================================================================

print("\nCreating combined dataset with DuckDB...")

# Create DuckDB connection
conn = duckdb.connect()

# Register the DataFrames as DuckDB tables
conn.register('los_angeles_df', los_angeles)
conn.register('chicago_df', chicago)
conn.register('philly_df', philly)

# Execute the UNION ALL query directly on the registered DataFrames
combined_data = conn.execute("""
    DROP TABLE IF EXISTS combined_data;

    CREATE TABLE combined_data AS
        -- Los Angeles
        SELECT
            city,
            "Date",
            "Time",
            month,
            day,
            is_weekend,
            "Location" as location,
            LAT as latitude,
            LON as longitude,
            nibrs_code,
            "Crm Cd Desc" as description,
            CLOSEST_STATION,
            CLOSEST_STATION_OBJECTID,
            DISTANCE_METERS
        FROM los_angeles_df
        WHERE YEAR("Date Rptd") = 2020
            AND "Date" IS NOT NULL
            AND nibrs_code IS NOT NULL

        UNION ALL

        -- Chicago
        SELECT
            city,
            "Date",
            "Time",
            month,
            day,
            is_weekend,
            "Block" as location,
            Latitude as latitude,
            Longitude as longitude,
            nibrs_code,
            Description as description,
            CLOSEST_STATION_NAME as CLOSEST_STATION,
            CLOSEST_STATION_OBJECTID,
            DISTANCE_METERS
        FROM chicago_df
        WHERE YEAR("Date") = 2020
            AND "Date" IS NOT NULL
            AND nibrs_code IS NOT NULL

        UNION ALL

        -- Philadelphia
        SELECT
            city,
            "Date",
            "Time",
            month,
            day,
            is_weekend,
            location_block as location,
            lat as latitude,
            lng as longitude,
            nibrs_code,
            text_general_code as description,
            CLOSEST_STATION_NAME as CLOSEST_STATION,
            CLOSEST_STATION_OBJECTID,
            DISTANCE_METERS
        FROM philly_df
        WHERE YEAR(dispatch_date_time) = 2020
            AND "Date" IS NOT NULL
            AND nibrs_code IS NOT NULL;

    SELECT * FROM combined_data;
""").fetchdf()

print(f"\nCombined dataset created with {len(combined_data)} records.")
print("\nFirst few rows:")
print(combined_data.head())

# Optional: Save the combined data to CSV
combined_data.to_csv('combined_crime_data_2020.csv', index=False)
print("\nCombined data saved to 'combined_crime_data_2020.csv")