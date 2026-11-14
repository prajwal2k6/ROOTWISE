
import re
from typing import Any


# Broad crop-family classification.
CROP_FAMILIES = {
    "cereal": [
        "rice", "paddy", "wheat", "maize", "corn",
        "ragi", "finger millet", "sorghum", "jowar",
        "bajra", "pearl millet", "barley", "oats",
    ],
    "legume": [
        "groundnut", "peanut", "soybean", "soya",
        "chickpea", "gram", "pigeon pea", "arhar",
        "tur", "lentil", "moong", "urad", "cowpea",
        "beans", "peas", "field pea", "green gram",
        "black gram",
    ],
    "oilseed": [
        "sunflower", "sesame", "safflower", "castor",
        "mustard",
    ],
    "solanaceae": [
        "tomato", "potato", "brinjal", "eggplant",
        "chilli", "pepper",
    ],
    "brassica": [
        "cabbage", "cauliflower", "broccoli", "radish",
    ],
    "cucurbit": [
        "cucumber", "pumpkin", "bottle gourd",
        "bitter gourd", "watermelon", "melon",
    ],
    "root_crop": [
        "carrot", "beetroot", "turnip",
        "sweet potato", "cassava",
    ],
}


# Preliminary candidates only. Local suitability must be checked.
CROP_CANDIDATES = {
    "cereal": [
        "Maize", "Finger millet", "Sorghum",
        "Pearl millet", "Wheat", "Rice",
    ],
    "legume": [
        "Green gram", "Black gram", "Cowpea",
        "Chickpea", "Lentil", "Field pea",
        "Pigeon pea", "Soybean", "Groundnut",
    ],
    "oilseed": [
        "Sunflower", "Sesame", "Safflower", "Mustard",
    ],
    "solanaceae": [
        "Potato", "Tomato", "Brinjal", "Chilli",
    ],
    "brassica": [
        "Cabbage", "Cauliflower", "Broccoli",
    ],
    "cucurbit": [
        "Cucumber", "Pumpkin", "Bottle gourd",
    ],
    "root_crop": [
        "Carrot", "Beetroot", "Turnip",
    ],
}


def _clean_crop_name(crop: str) -> str:
    return crop.strip().lower()


def _identify_crop_family(crop: str) -> str:
    normalized = _clean_crop_name(crop)

    # Match longer names first to avoid partial-name conflicts.
    for family, crops in CROP_FAMILIES.items():
        for known_crop in sorted(crops, key=len, reverse=True):
            if (
                normalized == known_crop
                or normalized.startswith(known_crop + " ")
                or normalized.endswith(" " + known_crop)
            ):
                return family

    return "unknown"


def _crop_details(crops: list[str]) -> list[dict]:
    """Return crop names with their broad family labels."""
    details = []

    for crop in crops:
        if crop == "Not recorded":
            family = "Not recorded"
        elif crop == "Crop selection required":
            family = "To be selected"
        else:
            family = _identify_crop_family(crop).replace(
                "_", " "
            ).title()

        details.append({
            "name": crop,
            "family": family,
        })

    return details


def _parse_crop_sequence(sequence: str | None) -> list[str]:
    if not sequence:
        return []

    parts = re.split(r"→|->|>|;|\n|,", sequence)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _parse_other_crops(other_crops: str | None) -> list[str]:
    if not other_crops:
        return []

    parts = re.split(r",|;|\n", other_crops)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _get_farm_information(farm: Any) -> dict:
    sequence = _parse_crop_sequence(
        getattr(farm, "previous_crop_sequence", None)
    )

    other_crops = _parse_other_crops(
        getattr(farm, "other_crops", None)
    )

    main_crop = getattr(farm, "main_crop", None)

    if main_crop:
        main_crop = main_crop.strip()

    if not sequence and main_crop:
        sequence = [main_crop]

    known_crops = list(dict.fromkeys(
        sequence + other_crops + ([main_crop] if main_crop else [])
    ))

    return {
        "farm_name": getattr(farm, "farm_name", "Your farm"),
        "area_acres": getattr(farm, "area_acres", None),
        "latitude": getattr(farm, "latitude", None),
        "longitude": getattr(farm, "longitude", None),
        "state": getattr(farm, "state", None),
        "district": getattr(farm, "district", None),
        "soil_type": getattr(farm, "soil_type", None),
        "irrigation": getattr(farm, "irrigation", None),
        "main_crop": main_crop,
        "other_crops": other_crops,
        "crop_sequence": sequence,
        "crop_frequency": getattr(farm, "crop_frequency", None),
        "sowing_season": getattr(farm, "sowing_season", None),
        "harvest_period": getattr(farm, "harvest_period", None),
        "priority": getattr(farm, "priority", None),
        "notes": getattr(farm, "notes", None),
        "known_crops": known_crops,
    }


def _get_profile_completeness(farm_data: dict) -> dict:
    fields = {
        "Main crop": farm_data["main_crop"],
        "Crop history": farm_data["crop_sequence"],
        "Soil type": farm_data["soil_type"],
        "Irrigation": farm_data["irrigation"],
        "Sowing season": farm_data["sowing_season"],
        "Harvest period": farm_data["harvest_period"],
        "Farm priority": farm_data["priority"],
        "Farm coordinates": (
            farm_data["latitude"] is not None
            and farm_data["longitude"] is not None
        ),
    }

    available = [
        name for name, value in fields.items() if value
    ]

    missing = [
        name for name, value in fields.items() if not value
    ]

    return {
        "available_count": len(available),
        "total_count": len(fields),
        "available_fields": available,
        "missing_fields": missing,
    }


def _choose_candidate(
    family: str,
    known_crops: list[str],
) -> str | None:
    """Choose a candidate not already present in the supplied crop list."""
    candidates = CROP_CANDIDATES.get(family, [])
    known = {_clean_crop_name(crop) for crop in known_crops}

    for crop in candidates:
        if _clean_crop_name(crop) not in known:
            return crop

    return None


def _choose_from_families(
    families: list[str],
    excluded_crops: list[str],
) -> str | None:
    """Try crop families in order until a new candidate is found."""
    for family in families:
        candidate = _choose_candidate(family, excluded_crops)

        if candidate:
            return candidate

    return None


def _build_three_crop_sequence(
    farm_data: dict,
    preferred_families: list[str],
) -> tuple[list[str], list[str]]:
    """
    Build three distinct preliminary crop phases.

    The selected crops are examples for further local screening,
    not confirmed agronomic recommendations.
    """
    main_crop = farm_data["main_crop"]
    known_crops = farm_data["known_crops"]

    first_crop = main_crop

    if not first_crop and farm_data["crop_sequence"]:
        first_crop = farm_data["crop_sequence"][0]

    if not first_crop and known_crops:
        first_crop = known_crops[0]

    if not first_crop:
        first_crop = "Crop selection required"

    crops = [first_crop]

    second_crop = _choose_from_families(
        preferred_families,
        known_crops + crops,
    )

    if second_crop:
        crops.append(second_crop)
    else:
        crops.append("Crop selection required")

    third_crop = _choose_from_families(
        [
            family for family in preferred_families
            if family != _identify_crop_family(second_crop or "")
        ] + ["cereal", "legume", "oilseed", "root_crop"],
        known_crops + crops,
    )

    if third_crop:
        crops.append(third_crop)
    else:
        crops.append("Crop selection required")

    return crops, preferred_families


def _make_pathway(
    number: str,
    strategy: str,
    title: str,
    crops: list[str],
    phase_reasons: list[str],
    purpose: str,
    summary: str,
    benefits: list[str],
    risks: list[str],
    checks: list[str],
    evidence: list[str],
    confidence_level: str,
    confidence_explanation: str,
) -> dict:
    # Keep exactly three phases. Do not silently remove repeated or
    # missing-history entries because each phase has its own meaning.
    crops = list(crops[:3])

    while len(crops) < 3:
        crops.append("Not recorded")

    return {
        "number": number,
        "strategy": strategy,
        "title": title,
        "sequence": " → ".join(crops),
        "crops": crops,
        "crop_details": _crop_details(crops),
        "phase_reasons": phase_reasons[:3],
        "purpose": purpose,
        "summary": summary,
        "benefits": benefits,
        "risks": risks,
        "checks": checks,
        "evidence": evidence,
        "confidence": {
            "level": confidence_level,
            "explanation": confidence_explanation,
        },
    }


def _build_existing_rotation(farm_data: dict) -> dict:
    sequence = farm_data["crop_sequence"][:3]

    if not sequence:
        sequence = ["Not recorded"]

    recorded_count = len(sequence)

    while len(sequence) < 3:
        sequence.append("Not recorded")

    phase_reasons = [
        "This crop is taken from the crop history saved in your farm profile."
        if index < recorded_count
        else "This phase is not available in your saved crop history."
        for index in range(3)
    ]

    return _make_pathway(
        number="01",
        strategy="existing_rotation",
        title="Existing Rotation",
        crops=sequence,
        phase_reasons=phase_reasons,
        purpose=(
            "Use your saved crop sequence as the baseline "
            "for comparing alternative rotations."
        ),
        summary=(
            "This pathway displays the crop history recorded in your "
            "farm profile. Missing phases are marked as not recorded."
        ),
        benefits=[
            "Reflects your existing farming practice.",
            "Provides a reference for comparing alternative rotations.",
            "May be familiar in terms of labour and farm management.",
        ],
        risks=[
            "Repeated crops from the same family may create rotation-related challenges.",
            "Actual soil and pest effects cannot be determined from crop names alone.",
        ],
        checks=[
            "Verify the order and duration of previous crops.",
            "Review pest and disease history.",
            "Check soil nutrient status.",
        ],
        evidence=[
            "Saved crop history",
            "Main crop and other crops in the farm profile",
        ],
        confidence_level="Profile-based",
        confidence_explanation=(
            "This reflects saved farm information. Missing phases are "
            "not assumed or filled with invented historical crops."
        ),
    )


def _build_soil_restoration_rotation(farm_data: dict) -> dict:
    main_crop = farm_data["main_crop"]
    main_family = (
        _identify_crop_family(main_crop)
        if main_crop else "unknown"
    )

    # Alternate between a legume and a cereal where possible.
    if main_family == "legume":
        preferred_families = ["cereal", "oilseed", "root_crop"]
    else:
        preferred_families = ["legume", "cereal", "oilseed"]

    crops, _ = _build_three_crop_sequence(
        farm_data,
        preferred_families,
    )

    phase_reasons = [
        (
            f"{crops[0]} represents the current or recorded starting crop. "
            "It provides the baseline for the proposed rotation."
        ),
        (
            f"{crops[1]} is selected as a different crop-family candidate. "
            "Legumes, when suitable, can contribute to biological nitrogen fixation."
        ),
        (
            f"{crops[2]} adds another crop phase to diversify the sequence. "
            "Its suitability and nutrient requirements need local verification."
        ),
    ]

    return _make_pathway(
        number="02",
        strategy="soil_restoration",
        title="Soil-Restoration Rotation",
        crops=crops,
        phase_reasons=phase_reasons,
        purpose=(
            "Explore crop-family diversification and possible soil-health "
            "benefits across three crop phases."
        ),
        summary=(
            "The pathway prioritises a different crop family after the "
            "starting crop. A legume phase may support nitrogen fixation, "
            "but the actual benefit depends on crop, soil and management."
        ),
        benefits=[
            "Legume phases may contribute to biological nitrogen fixation.",
            "Different crop families can diversify the rotation.",
            "Suitable cover crops may help protect exposed soil.",
        ],
        risks=[
            "Crop suitability depends on local climate, soil and variety.",
            "Some crops may compete for limited water.",
            "New crops may require additional labour, seed and market access.",
        ],
        checks=[
            "Check local crop and variety suitability.",
            "Review soil pH, organic matter and nutrient levels.",
            "Check water availability during each proposed crop period.",
            "Consider local pest and disease history.",
        ],
        evidence=[
            "Saved crop history",
            "Other crops recorded in the farm profile",
            "Broad crop-family classification",
        ],
        confidence_level="Preliminary candidate",
        confidence_explanation=(
            "Crop candidates are selected using broad crop-family rules. "
            "Soil tests and local agronomic validation are needed."
        ),
    )


def _build_climate_resilience_rotation(farm_data: dict) -> dict:
    main_crop = farm_data["main_crop"]
    main_family = (
        _identify_crop_family(main_crop)
        if main_crop else "unknown"
    )

    if main_family == "cereal":
        preferred_families = ["oilseed", "legume", "root_crop"]
    elif main_family == "legume":
        preferred_families = ["cereal", "oilseed", "root_crop"]
    else:
        preferred_families = ["legume", "cereal", "oilseed"]

    crops, _ = _build_three_crop_sequence(
        farm_data,
        preferred_families,
    )

    phase_reasons = [
        (
            f"{crops[0]} is the starting crop from your farm profile "
            "or recorded crop information."
        ),
        (
            f"{crops[1]} introduces a different crop-family candidate. "
            "Its growing-season and water requirements must be checked."
        ),
        (
            f"{crops[2]} provides a third phase for comparing crop options "
            "under local rainfall and irrigation conditions."
        ),
    ]

    return _make_pathway(
        number="03",
        strategy="climate_resilience",
        title="Climate-Resilience Rotation",
        crops=crops,
        phase_reasons=phase_reasons,
        purpose=(
            "Explore crop-family diversification while considering "
            "rainfall, temperature and available irrigation."
        ),
        summary=(
            "This pathway proposes three preliminary crop phases. "
            "NASA climate observations and local growing-season rules "
            "must be checked before treating the crops as suitable."
        ),
        benefits=[
            "Introduces different crop families.",
            "Can help explore alternatives for different growing seasons.",
            "Can support comparison of crop water requirements.",
        ],
        risks=[
            "Historical climate patterns do not guarantee future conditions.",
            "Satellite data may not represent exact field-level conditions.",
            "Crop suitability also depends on variety, soil and management.",
            "Changing crops may affect market access and farm income.",
        ],
        checks=[
            "Evaluate local temperature and rainfall patterns.",
            "Check growing-season length and sowing windows.",
            "Compare crop water requirements with available irrigation.",
            "Review local drought and excess-rainfall risks.",
        ],
        evidence=[
            "Saved farm coordinates",
            "Saved irrigation method",
            "Saved sowing and harvest periods",
            "Climate suitability screening pending",
        ],
        confidence_level="Awaiting climate validation",
        confidence_explanation=(
            "No climate suitability score is claimed. Climate observations "
            "and local crop rules must be integrated before final crop selection."
        ),
    )


def build_rotation_recommendations(farm: Any) -> dict:
    """Generate three preliminary crop rotation pathways."""
    farm_data = _get_farm_information(farm)

    completeness = _get_profile_completeness(farm_data)

    pathways = [
        _build_existing_rotation(farm_data),
        _build_soil_restoration_rotation(farm_data),
        _build_climate_resilience_rotation(farm_data),
    ]

    return {
        "farm": {
            "id": getattr(farm, "id", None),
            "name": farm_data["farm_name"],
            "area_acres": farm_data["area_acres"],
            "main_crop": farm_data["main_crop"],
            "soil_type": farm_data["soil_type"],
            "irrigation": farm_data["irrigation"],
            "state": farm_data["state"],
            "district": farm_data["district"],
            "sowing_season": farm_data["sowing_season"],
            "harvest_period": farm_data["harvest_period"],
            "current_sequence": farm_data["crop_sequence"],
            "priority": farm_data["priority"],
        },
        "profile_completeness": completeness,
        "comparison_status": (
            "Preliminary crop-family comparison. "
            "Local agronomic and climate validation is pending."
        ),
        "scoring": {
            "available": False,
            "reason": (
                "Comparative scores will be introduced after climate "
                "evidence and locally validated crop suitability rules "
                "have been integrated."
            ),
        },
        "pathways": pathways,
        "limitations": [
            "Crop-family classification is broad.",
            "Candidate crops are not guaranteed recommendations.",
            "Local soil testing and agronomic guidance are required.",
            "Climate suitability has not yet been evaluated.",
            "Missing historical crops are marked as not recorded.",
        ],
    }
