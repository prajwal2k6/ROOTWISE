# ROOTWISE M2/M3 Integration

The M2/M3 backend uses ROOTWISE's existing `DATABASE_URL`, SQLAlchemy `Base`,
engine, session and `Farmer` model. Its models are registered through
`backend/app/models/__init__.py`. The teammate `Farmer` schema and second engine
are not used.

## Database

The migrations add regions, fields, crops, rotations, climate features, map
cells, scenarios and layer metadata. They reference the existing
`farmers.id`; they do not create, alter or replace the `farmers` table. The
models store GeoJSON in PostgreSQL JSONB and do not require PostGIS. Use the
existing PostgreSQL/Supabase database URL and inspect the target schema before
the first migration.

From `backend`, after installing `requirements.txt`, bootstrap only the
existing ROOTWISE `Farmer` and `Farm` tables (a no-op when they already exist),
then apply the additive schema:

```powershell
python -m scripts.bootstrap_database
python -m alembic upgrade head
```

The historical Bengaluru pilot can then be loaded explicitly from the project
root with:

```powershell
python backend/scripts/ingest_m2_snapshot.py
```

This imports the bundled **2016-01-01** observation snapshot. It is historical
data, not a live feed. The source metadata and missing NDVI/ET values are
preserved. The script is a local administrative operation and is not exposed
as an unauthenticated API route.

## APIs

All new read APIs use `/api/v1`:

- `GET /api/v1/health` — checks the shared database connection.
- `GET /api/v1/regions` and `/api/v1/regions/{region_id}` — read-only region
  catalog.
- `GET /api/v1/crops` and `/api/v1/crops/{crop_id}` — read-only crop catalog.
- Authenticated `GET`, `POST`, `PATCH`, and `DELETE /api/v1/fields` routes,
  scoped to the existing farmer profile; submitted payloads cannot set owner IDs.
- `GET /api/v1/climate/regions/{region_code}/observations` and `/dates`.
- `GET /api/v1/maps/regions/{region_code}/cells` and
  `/cells/{cell_code}`.
- `GET /api/v1/risk/regions/{region_code}/summary`, `/cells`, and
  `/cells/{cell_code}`. These report stored risk values only; no risk
  calculation is performed.
- `GET /api/v1/timeseries/regions/{region_code}/climate` and `/indicators`.
- `POST /api/v1/recommendations/` — M3 recommendation using only a field
  belonging to the authenticated ROOTWISE farmer profile. The authenticated
  account email must match an existing `farmers.email` record and that farmer
  must own the M2 field. Historical observations are not converted into
  current-season conditions.

Field creation and M3 recommendation require a pre-existing local
`farmers.email` profile matching the authenticated Supabase email. The main
frontend's existing farm onboarding writes to its separate `farms` model and
does not create these M2 field records or local Farmer profiles.

Existing ROOTWISE frontend files are unchanged. No existing page currently
provides a supported M2 region or M2 field selection flow, so these APIs are
available to future clients without changing the existing UI.

## Pipeline rebuild requirements and limits

The original M2 processing scripts are under `scripts/`. Optional processing
dependencies are listed in `backend/requirements-m2-pipeline.txt`. The branch
contains final pilot exports and validation reports, but not the raw NASA
rasters or district-boundary inputs needed to reproduce every processing
stage. Some acquisition steps also require NASA Earthdata/AppEEARS access.
Obtain those inputs and credentials before attempting a full rebuild. Do not
commit credentials or treat the bundled dated snapshot as current data.

The source branch's layer/glossary APIs and layer service are empty. Its
simulation service persists pending scenario records but does not calculate
results. Those endpoints are not registered. The field/crop/region write APIs
and ingestion endpoint were not registered as-is because the source versions
lack appropriate authorization. Field CRUD was replaced by an authenticated,
owner-scoped router. Crop and region mutation remains unavailable; the
ingestion operation is a local administrative command.
