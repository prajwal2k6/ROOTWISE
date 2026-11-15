
from rootwise_engine.models import Climate


def build_seasonal_climate(
    environmental_data: dict,
    seasonal_inputs: dict | None = None,
) -> Climate:
    """
    Build M1 climate inputs.

    Historical M2 observations are not automatically
    treated as current-season measurements.
    """
    if seasonal_inputs is None:
        return Climate(
            data_kind="missing",
            notes=[
                "M2 historical observations are available separately.",
                "Verified seasonal climate inputs are unavailable.",
            ],
        )

    required = (
        "source_id",
        "source_url",
        "data_kind",
        "seasonal_effective_rainfall_mm",
        "seasonal_irrigation_mm",
        "seasonal_etc_by_crop_mm",
    )

    missing = [
        key for key in required
        if seasonal_inputs.get(key) is None
    ]

    if missing:
        raise ValueError(
            f"Missing seasonal climate inputs: {missing}"
        )

    if seasonal_inputs["data_kind"] not in (
        "observed",
        "modelled",
    ):
        raise ValueError(
            "Seasonal inputs must be observed or modelled"
        )

    if not seasonal_inputs["source_id"] or not seasonal_inputs["source_url"]:
        raise ValueError("Seasonal inputs require source provenance")

    return Climate(
        source_id=seasonal_inputs["source_id"],
        source_url=seasonal_inputs["source_url"],
        data_kind=seasonal_inputs["data_kind"],
        seasonal_effective_rainfall_mm=seasonal_inputs[
            "seasonal_effective_rainfall_mm"
        ],
        seasonal_irrigation_mm=seasonal_inputs[
            "seasonal_irrigation_mm"
        ],
        seasonal_etc_by_crop_mm=seasonal_inputs[
            "seasonal_etc_by_crop_mm"
        ],
        notes=[
            "Seasonal inputs supplied by an external verified source.",
            "Historical M2 observations are retained separately.",
        ],
    )
