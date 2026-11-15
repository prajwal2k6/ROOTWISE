# ROOTWISE M2 – NASA MODIS MOD16A2 Evapotranspiration Integration Plan (Revised)

## 1. Product Identification & Collection

| Parameter | Specification | Details |
|---|---|---|
| **Product Short Name** | `MOD16A2GF` | MODIS/Terra Net Evapotranspiration Gap-Filled 8-Day L4 Global 500m SIN Grid |
| **Collection / Version** | `061` (Collection 6.1) | Current operational standard (DOI: [10.5067/MODIS/MOD16A2GF.061](https://doi.org/10.5067/MODIS/MOD16A2GF.061)) |
| **Historical Archive Nature** | **Year-End Gap-Filled (`MOD16A2GF`)** | For historical years (2000–2020, including **2016**), NASA LP DAAC archives the official gap-filled science product `MOD16A2GF.061`. Operational non-gap-filled `MOD16A2.061` is only generated forward (2021–present). |
| **Meaning of "Gap-Filled"** | **LAI/FPAR Input Interpolation Only** | The gap-filling specifically resolves missing or cloud-contaminated **MOD15A2H LAI/FPAR inputs** using temporal climatology and interpolation before running the Penman-Monteith algorithm. **It does NOT mean all land pixels have valid ET.** Non-vegetated surfaces, water bodies, and urban/built-up land cover (`32762`) are still intentionally not modeled and remain un-filled. |
| **Temporal Granularity** | 8-day composite | 46 composite periods per calendar year |
| **Target Composite Period** | **2016-01-01 to 2016-01-08** | Day of Year `2016001` (8 days inclusive: Jan 1 00:00:00 to Jan 8 23:59:59 UTC) |
| **Sinusoidal Grid Tile** | **`h25v07`** | Covers 10°N–20°N, ~71.8°E–82.1°E (completely encloses Bengaluru Urban) |
| **Exact NASA Granule** | `MOD16A2GF.A2016001.h25v07.061.2022001123906` | Published in LPCLOUD archive |

---

## 2. Variables, Units & Scale Factor

| Science Dataset Layer | Data Type | Units | Scale Factor | Physical Meaning |
|---|---|---|---|---|
| **`ET_500m`** (Primary) | `int16` | $\text{kg/m}^2/\text{8-day} \equiv \text{mm/8-day}$ | `0.1` | **8-day accumulated evapotranspiration** |
| **`ET_QC_500m`** (Quality) | `uint8` | Bit field (0–255) | None (1) | Algorithm and cloud quality flags |
| **`PET_500m`** (Potential ET) | `int16` | $\text{kg/m}^2/\text{8-day} \equiv \text{mm/8-day}$ | `0.1` | 8-day potential evapotranspiration |
| **`LE_500m`** (Latent Heat) | `int16` | $\text{MJ/m}^2/\text{day}$ | `0.01` | Average latent heat flux |

### Critical Physical Distinction: 8-Day Accumulated ET vs. Daily ET
- **Native Unit**: $1\text{ kg/m}^2$ of water over a $1\text{ m}^2$ area equals exactly $1\text{ mm}$ depth of water ($1\text{ kg/m}^2/\text{8-day} \equiv 1\text{ mm/8-day}$).
- **Temporal Accumulation**: `ET_500m` represents the **total evapotranspiration accumulated over the 8-day composite period** (Jan 1 to Jan 8, 2016), **NOT** a single-day measurement.
  $$\text{ET}_{\text{accum\_8day\_mm}} = \text{Raw} \times 0.1$$
- **Daily Average Rate Equivalent**:
  $$\text{ET}_{\text{daily\_avg\_mm/day}} = \frac{\text{Raw} \times 0.1}{8}$$
- **Indicator Retention**: `evapotranspiration_mm` in our schema directly stores the native **8-day accumulated total ($\text{mm/8-day}$)** to preserve physical integrals without synthetic daily disaggregation. Metadata explicitly records `units: "mm/8day (accumulated over 8-day composite 2016-01-01 to 2016-01-08)"` and provides the daily divisor ($8$).

---

## 3. Valid Range, Special Fill Codes & Negative Value Preservation

Per the official NASA MOD16 Collection 6.1 User Guide, `ET_500m` values are structured as follows:

| Stored Raw Range / Code | Physical Equivalent ($\text{mm/8-day}$) | Category / Surface Class | Handling in ROOTWISE Pipeline |
|---|---|---|---|
| **`-32767` to `32700`** | **`-3276.7` to `+3270.0`** | **Valid physical ET data** | **Preserved and scaled ($\times 0.1$)** |
| **`32761`** | — | Unclassified land cover | Special code $\to$ `null` |
| **`32762`** | — | **Urban or Built-up land cover** | **Special code $\to$ `null`** (model does not retrieve ET) |
| **`32763`** | — | Permanent wetland | Special code $\to$ `null` |
| **`32764`** | — | Permanent snow and ice | Special code $\to$ `null` |
| **`32765`** | — | Barren or sparsely vegetated | Special code $\to$ `null` |
| **`32766`** | — | Water body | Special code $\to$ `null` |
| **`32767`** | — | Nodata fill value | Nodata fill $\to$ `null` |

### Physical Validity Policy:
1. **Preserve Valid Negative Raw Values**: Negative raw values in the documented range `[-32767, 32700]` represent valid model states (e.g. condensation, dew formation, or boundary fluxes) and **must NOT be rejected by an artificial `raw >= 0` check**.
2. **Exclude Special Non-Vegetated Codes**: Only the discrete integer codes `32761` through `32767` (and actual nodata) are treated as invalid/unretrieved and converted to `null`.
3. **Validity Condition**:
   $$\text{is\_valid\_raw\_et} = (\text{raw\_et} \ge -32767) \ \land \ (\text{raw\_et} \le 32700) \ \land \ (\text{raw\_et} \notin [32761, 32767]) \ \land \ (\text{math.isfinite}(\text{raw\_et}))$$

---

## 4. Transparent Quality Control (QC) Policy for `MOD16A2GF`

The `ET_QC_500m` layer is an 8-bit unsigned integer (`uint8`):
* **Bit 0 (MODLAND_QC)**:
  * `0` = Primary/unfilled LAI/FPAR input used.
  * `1` = Climatology/gap-filled LAI/FPAR input used.
* **Bits 3–4 (Cloud State)**: Cloud presence flags (`00` = Clear, `01` = Cloud, `10` = Mixed cloud, `11` = Assumed clear).
* **Bits 5–7 (SCF_QC)**: 5-level method score (`000` = Main RT method, `001` = Main RT with saturation, `010`/`011` = Empirical, `100` = Not produced).

### Official NASA Guideline for `MOD16A2GF`:
The NASA MOD16 Collection 6.1 User Guide states:
> *"Users can ignore the QC layer for the improved year-end gap-filled product (MOD16A2GF) because all poor-quality LAI/FPAR pixels have already been filled through the gap-filling procedure."*

Rejecting pixels with `Bit 0 == 1` would erroneously discard valid gap-filled retrievals that the `MOD16A2GF` product was specifically designed to provide.

### Proposed Transparent Quality Policy:
1. **Primary Validity Screen**: Use the documented valid raw range `[-32767, 32700]` and exclusion of special codes `[32761, 32767]` as the primary validity check.
2. **QC Preservation for Diagnostics**: Read and preserve `ET_QC_500m` for all pixels to inspect diagnostic data.
3. **Distribution Reporting**: Report the exact breakdown across all 2,380 grid cells:
   - Primary LAI retrieval count (`Bit 0 == 0`)
   - Gap-filled LAI retrieval count (`Bit 0 == 1`)
   - Cloud state distribution (Bits 3–4)
4. **Stricter QC Subsets Documented Separately**: Document the count of pure primary retrievals (`Bit 0 == 0`) separately in metadata and integration logs without discarding valid gap-filled observations.

---

## 5. Temporal Coverage

- **Observation Date in ROOTWISE**: `2016-01-01`
- **Composite Span**: 8 calendar days, starting **2016-01-01 00:00:00 UTC** through **2016-01-08 23:59:59 UTC**
- **Julian Identifier**: `A2016001`
- `2016-01-01` represents Day 1 of this 8-day accumulation window.

---

## 6. NASA AppEEARS Download Settings & File Structure

Using the validated district boundary GeoJSON:
[`data/raw/modis/bengaluru_urban_boundary.geojson`](file:///C:/Users/Manish%20S/OneDrive/Desktop/ROOTWISE/data/raw/modis/bengaluru_urban_boundary.geojson)

### AppEEARS Request Configuration
- **Task Type**: Area Request
- **Boundary**: Upload `bengaluru_urban_boundary.geojson`
- **Product**: `MOD16A2GF.061` (Net Evapotranspiration Gap-Filled 8-Day L4 Global 500m)
- **Date Range**: `01-01-2016` to `01-08-2016`
- **Layers**:
  1. `ET_500m` (Total Evapotranspiration)
  2. `ET_QC_500m` (Quality Control Flags)
  3. *(Optional)* `PET_500m` (Potential Evapotranspiration)
- **Output Format**: `geotiff`
- **Output Projection**: `geographic` (`EPSG:4326`)

### Expected Staged Files under `data/raw/modis/`
```
data/raw/modis/
├── MOD16A2GF.061__500m_8_days_ET_doy2016001000000_aid0001.tif       (~25 KB)
├── MOD16A2GF.061__500m_8_days_ET_QC_doy2016001000000_aid0001.tif    (~5 KB)
└── MOD16A2GF-061-request-metadata.json                              (~5 KB)
```
Total download size is **under 100 KB**.

---

## 7. GeoTIFF Format & Expected CRS

- **Format**: Cloud-optimized standard GeoTIFF (`.tif`), natively supported on Windows via `rasterio`.
- **Expected CRS**: `EPSG:4326` (WGS84 lat/lon).
- **Pixel Spacing**: Approximately $0.00416667^\circ$ (~463.3 m) at 500 m nominal resolution.
- **Raster Dimensions**: Approximately $123 \text{ rows} \times 138 \text{ columns} \approx 17,000 \text{ pixels}$ covering the district.

---

## 8. Spatial Mapping to 2,380 1 km Grid Cells

At 500 m nominal resolution, each $1\text{ km} \times 1\text{ km}$ cell contains approximately **4 MODIS pixels** ($2 \times 2$ grid):

1. **Centroid Point Sampling (Primary)**:
   - Query the 500 m pixel covering `(centroid_lat, centroid_lon)`.
   - If pixel is valid ($-32767 \le \text{raw} \le 32700$ and $\text{raw} \notin [32761, 32767]$), assign:
     $$\text{evapotranspiration\_mm} = \text{round}(\text{raw} \times 0.1, 4)$$
2. **Within-Cell Polygon Fallback (Secondary)**:
   - If the centroid pixel is urban (`32762`), water (`32766`), or fill (`32767`), query all 500 m pixel centers falling strictly inside that 1 km cell polygon.
   - If $\ge 1$ valid pixels exist inside the cell, assign their arithmetic mean:
     $$\text{evapotranspiration\_mm} = \text{round}\left(\frac{1}{N}\sum_{i=1}^N \text{raw}_i \times 0.1, 4\right)$$
3. **Strict Null Retention**:
   - If all pixels inside the 1 km cell polygon are urban (`32762`), barren (`32765`), water (`32766`), or fill (`32767`), the cell remains `null`.
   - **Under NO circumstances are pixels outside the cell polygon borrowed.**

---

## 9. Handling Missing & Low-Quality Pixels

- **No Spatial Interpolation**: Pixels flagged with special non-vegetated codes (`32761`–`32767`) are left as `null`. No synthetic values, distance-weighted averages, or regional smoothing will be applied.
- **Distinction from Zero**: An urban cell where ET is not modeled is `null`, **not `0.0`**. `0.0 mm` indicates zero measured evaporation from a vegetated surface, whereas `null` indicates that the satellite algorithm does not retrieve ET over impervious urban cover.

---

## 10. Proposed Metadata Schema & Validation Suite

### Proposed `indicator_metadata["evapotranspiration_mm"]`
```json
{
  "source": "NASA MODIS Terra MOD16A2GF Version 061 (8-Day L4 Global 500m)",
  "variable": "ET_500m",
  "units": "mm/8day (accumulated over 8-day composite)",
  "scale_factor": 0.1,
  "status": "observed",
  "native_resolution": "500 m Sinusoidal Grid (~463.31 m x 463.31 m)",
  "temporal_coverage": "2016-01-01 to 2016-01-08 (8-day composite, DOY 001-008)",
  "temporal_accumulation": "8-day total (not daily ET rate)",
  "tile": "h25v07",
  "valid_raw_range": "-32767 to 32700",
  "physical_valid_range": "-3276.7 to 3270.0 mm/8day",
  "special_fill_codes": "32761 (unclassified), 32762 (urban), 32763 (wetland), 32764 (snow), 32765 (barren), 32766 (water), 32767 (fill)",
  "quality_policy": "Documented valid raw range excluding special codes 32761-32767. ET_QC_500m Bit 0 recorded for diagnostics per NASA MOD16 GF user guide.",
  "assignment_method": "Centroid 500m pixel sampling, with within-cell 500m pixel mean fallback; null otherwise",
  "direct_centroid_cells": "<count>",
  "fallback_within_cell_cells": "<count>",
  "null_cells": "<count>",
  "note": "8-day accumulated evapotranspiration from NASA MODIS/Terra MOD16A2GF Collection 6.1. Values represent total evapotranspiration in mm accumulated over the 8-day period from 2016-01-01 through 2016-01-08; they are NOT single-day rates. Urban built-up areas (code 32762) where the Penman-Monteith model does not retrieve transpiration are strictly retained as null without spatial interpolation."
}
```

### Safety & Validation Checklist
1. **Pre-flight Checks**: Verify 2,380 cells, unique IDs, CRS (`EPSG:4326`), date (`2016-01-01`), and confirm all 6 previously integrated indicators remain uncorrupted.
2. **Backup**: Create timestamped backup `bengaluru_urban_20160101_backup_YYYYMMDD_HHMMSS.json`.
3. **Atomic Write**: Write to `.tmp` file and atomically replace target file.
4. **Sample Refresh**: Refresh `data/outputs/bengaluru_urban_sample_3_cells.json`.
5. **Validator Execution**: Run `scripts/validate_bengaluru_json.py` to confirm 100% compliance.
