# Data sources of the files in `DATA/`

| File | Source (URL) | Downloaded | Licence / terms | How it was made |
|---|---|---|---|---|
| `stations_tennet_arcgis.csv` | TenneT ArcGIS feature service *TenneT Assets Hoogspanning*, layer 5 (stations): `https://services-eu1.arcgis.com/WjozPuR5ROn6NZE8/arcgis/rest/services/TenneT_Assets_Hoogspanning/FeatureServer/5` (ArcGIS item `02d4cfaf2a9241b68f9520748081d7e9`, owner TenneTTSO) | 13 October 2026 | Item licence: "Alle rechten voorbehouden. TenneT TSO B.V." (all rights reserved); copyright TenneT TSO B.V.; contact tennetCCC@tennet.eu. No open-data licence is stated. | Query `where=1=1`, `outFields=STATIONID,OBJECTOMSCHRIJVING`, `returnCentroid=true`, `outSR=28992` (RD New), paged by OBJECTID; one row per station: `station_id`, `station_name`, centroid `x_rd`, `y_rd` (371 stations). |
| `ip26_line_endpoints.csv` | TenneT ArcGIS feature service *TenneT investeringsplan 2026 projecten*, layer 1 (IP26_line): `https://services-eu1.arcgis.com/WjozPuR5ROn6NZE8/arcgis/rest/services/TenneT_investeringsplan_2026_projecten/FeatureServer/1` (ArcGIS item `0b6ab56945f5421f9e6afedcd47ad38e`, owner TenneTTSO) | 13 October 2026 | Item licence: "Alle rechten zijn voorbehouden aan TenneT TSO BV." (all rights reserved); contact geoinfo@tennet.eu. No open-data licence is stated. | Query of the line geometry with `outSR=28992`, `maxAllowableOffset=500`, `geometryPrecision=0` (generalised to 500 m, whole metres), paged by OBJECTID; per OBJECTID and path the first and last vertex (`x_start, y_start, x_end, y_end`) and the vertex count. |

Notes
- Both layers are published by TenneT TSO B.V. with "all rights reserved". Check with TenneT (or the project's
  data agreement) before redistributing these files in the repository; storing them only locally is the safe default.
- `IP26_line.xlsx` and `IP26_point.xlsx` are exports of layers 1 and 0 of the same IP2026 service (same terms).
- Used for verification only, not stored in `DATA/`: TenneT conductor layers `TenneT_Assets_Hoogspanning/FeatureServer/2`
  (overhead) and `/3` (cable), queried around the line ends; TenneT grid maps June 2026 (tennet.eu).
