
import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen


POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal"


def _fetch_power(endpoint: str, parameters: dict) -> dict:
    """Fetch JSON data from NASA POWER."""
    url = f"{POWER_BASE_URL}/{endpoint}/point?{urlencode(parameters)}"

    request = Request(
        url,
        headers={
            "User-Agent": "ROOTWISE-Agriculture-Platform/1.0"
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        parameter_data = (
            result.get("properties", {})
            .get("parameter", {})
        )

        if not parameter_data:
            raise RuntimeError(
                "NASA POWER returned no parameter data."
            )

        return parameter_data

    except Exception as exc:
        raise RuntimeError(
            f"NASA POWER request failed: {exc}"
        ) from exc


def _format_series(data: dict) -> dict:
    """Convert NASA's date-keyed values into frontend records."""
    formatted = {}

    for parameter, values in data.items():
        if not isinstance(values, dict):
            continue

        formatted[parameter] = [
            {
                "date": timestamp,
                "value": value,
            }
            for timestamp, value in sorted(values.items())
            if value is not None and value != -999
        ]

    return formatted


def get_nasa_farm_data(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Retrieve environmental data for a farm.

    Active source:
        NASA POWER - daily meteorological observations.

    Separate NASA datasets:
        SMAP - requires Earthdata integration.
        GPM IMERG - requires Earthdata integration.

    POWER precipitation is not labelled as GPM IMERG.
    """

    today = date.today()

    # Buffer recent daily observations.
    daily_end = today - timedelta(days=7)
    daily_start = daily_end - timedelta(days=364)

    daily_start_text = daily_start.strftime("%Y%m%d")
    daily_end_text = daily_end.strftime("%Y%m%d")

    results = {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "weather": {},
        "soil_moisture": {},
        "satellite_rainfall": {},
        "sources": {
            "NASA_POWER": "pending",
            "SMAP": "not_configured",
            "GPM_IMERG": "not_configured",
        },
        "source_details": {
            "NASA_POWER": {
                "dataset": "NASA POWER Daily API",
                "status": "pending",
                "description": (
                    "Daily meteorological observations."
                ),
            },
            "SMAP": {
                "dataset": "NASA Soil Moisture Active Passive",
                "status": "not_configured",
                "description": (
                    "Requires separate NASA Earthdata integration. "
                    "Not available through the POWER parameters used here."
                ),
            },
            "GPM_IMERG": {
                "dataset": "NASA GPM IMERG",
                "status": "not_configured",
                "description": (
                    "Requires separate NASA Earthdata integration. "
                    "POWER precipitation is not GPM IMERG."
                ),
            },
        },
        "warnings": [],
    }

    # 1. NASA POWER weather observations.
    try:
        weather = _fetch_power(
            "daily",
            {
                "parameters": (
                    "T2M,T2M_MAX,T2M_MIN,"
                    "PRECTOTCORR,RH2M,"
                    "ALLSKY_SFC_SW_DWN"
                ),
                "community": "AG",
                "longitude": longitude,
                "latitude": latitude,
                "start": daily_start_text,
                "end": daily_end_text,
                "format": "JSON",
            },
        )

        results["weather"] = _format_series(weather)
        results["sources"]["NASA_POWER"] = "available"
        results["source_details"]["NASA_POWER"]["status"] = (
            "available"
        )

    except Exception as exc:
        results["weather"] = {}
        results["sources"]["NASA_POWER"] = "unavailable"
        results["source_details"]["NASA_POWER"]["status"] = (
            "unavailable"
        )
        results["warnings"].append(str(exc))

    # 2. SMAP is deliberately not requested through NASA POWER.
    # It needs its own Earthdata product and access implementation.
    results["soil_moisture"] = {}

    # 3. GPM IMERG is deliberately not requested through NASA POWER.
    # It needs its own Earthdata product and access implementation.
    results["satellite_rainfall"] = {}

    results["warnings"].append(
        "SMAP soil moisture integration is not configured yet."
    )

    results["warnings"].append(
        "GPM IMERG rainfall integration is not configured yet."
    )

    return results
