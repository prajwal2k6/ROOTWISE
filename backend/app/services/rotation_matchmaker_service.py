
import re
from typing import Any


# Crop-family classification for common crops.
# These are broad botanical classifications, not local suitability rules.

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
        "beans", "peas", "field pea",
    ],
    "solanaceae": [
        "tomato", "potato", "brinjal", "eggplant",
        "chilli", "pepper",
    ],
    "brassica": [
        "cabbage", "cauliflower", "mustard",
        "broccoli", "radish",
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


def _clean_crop_name(crop: str) -> str:
    """Normalize a crop name for classification."""
    return crop.strip().lower()


def _identify_crop_family(crop: str) -> str:
    """Identify a broad crop family where possible."""
    normalized = _clean_crop_name(crop)

    for family, crops in CROP_FAMILIES.items():
        for known_crop in crops:
            if normalized == known_crop or normalized.startswith(
                known_crop + " "
            ):
                return family

    return "unknown"


def _parse_crop_sequence(sequence: str | None) -> list[str]:
    """Extract crop names from a saved crop sequence."""
    if not sequence:
        return []

    parts = re.split(r"→|->|>|;|\n", sequence)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _parse_other_crops(other_crops: str | None) -> list[str]:
    """Extract additional crops from the farm profile."""
    if not other_crops:
        return []

    parts = re.split(r",|;|\n", other_crops)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _get_farm_information(farm: Any) -> dict:
    """Collect the relevant information from a saved farm."""
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
    """Check how much information is available for decision support."""
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
        name for name, value in fields.items()
        if value
    ]

    missing = [
        name for name, value in fields.items()
        if not value
    ]

    return {
        "available_count": len(available),
        "total_count": len(fields),
        "available_fields": available,
        "missing_fields": missing,
    }


def _build_existing_rotation(farm_data: dict) -> dict:
    """Build the farmer's current rotation as the baseline."""
    sequence = farm_data["crop_sequence"]

    if sequence:
        sequence_text = " → ".join(sequence)
    else:
        sequence_text = "Crop history not provided"

    return {
        "number": "01",
        "strategy": "existing_rotation",
        "title": "Existing Rotation",
        "sequence": sequence_text,
        "purpose": (
            "Use your existing crop sequence as the baseline "
            "for comparing alternative rotation strategies."
        ),
        "summary": (
            "This pathway represents the crop sequence already "
            "recorded in your farm profile."
        ),
        "benefits": [
            "Reflects your existing farming practice.",
            "Provides a reference for comparing alternative rotations.",
            "May be familiar in terms of labour and farm management.",
        ],
        "risks": [
            "Repeated crops from the same family may create "
            "rotation-related challenges.",
            "The actual soil and pest effects cannot be determined "
            "from crop names alone.",
        ],
        "checks": [
            "Verify the order and duration of previous crops.",
            "Review pest and disease history.",
            "Check soil nutrient status.",
        ],
        "evidence": [
            "Saved crop history",
            "Main crop and other crops in the farm profile",
        ],
        "confidence": {
            "level": "Profile-based",
            "explanation": (
                "This pathway reflects saved farm information. "
                "It is not a measurement of crop performance."
            ),
        },
    }


def _build_soil_restoration_rotation(farm_data: dict) -> dict:
    """Build a candidate rotation that explores soil-restoration phases."""
    sequence = farm_data["crop_sequence"]
    known_crops = farm_data["known_crops"]

    main_crop = (
        farm_data["main_crop"]
        or (sequence[0] if sequence else None)
    )

    legume_crops = [
        crop for crop in known_crops
        if _identify_crop_family(crop) == "legume"
    ]

    next_crop = sequence[1] if len(sequence) > 1 else None

    if main_crop and legume_crops:
        legume_phase = " / ".join(legume_crops)
        proposed_sequence = (
            f"{main_crop} → locally suitable legume phase "
            f"({legume_phase})"
        )

        if next_crop:
            proposed_sequence += f" → {next_crop}"

        candidate_note = (
            "A legume is already listed in your farm profile. "
            "Its suitability as a rotation phase still needs local "
            "agronomic verification."
        )

    elif main_crop:
        proposed_sequence = (
            f"{main_crop} → locally suitable legume or cover crop "
            "→ next planned crop"
        )

        candidate_note = (
            "No legume phase was identified in the saved crop list. "
            "A locally suitable option needs to be selected."
        )

    else:
        proposed_sequence = (
            "Existing crop → locally suitable legume or cover crop "
            "→ next planned crop"
        )

        candidate_note = (
            "A main crop is needed before a more specific sequence "
            "can be evaluated."
        )

    return {
        "number": "02",
        "strategy": "soil_restoration",
        "title": "Soil-Restoration Rotation",
        "sequence": proposed_sequence,
        "purpose": (
            "Explore whether introducing suitable legumes, cover "
            "crops and different crop families could improve "
            "crop-sequence diversity and support soil management."
        ),
        "summary": candidate_note,
        "benefits": [
            "Legume phases may contribute to biological nitrogen "
            "fixation under suitable conditions.",
            "Different crop families can diversify the rotation.",
            "Suitable cover crops may help protect exposed soil.",
            "Different root patterns can be explored for soil management.",
        ],
        "risks": [
            "Legume suitability depends on local climate, soil and variety.",
            "Some cover crops may compete for limited water.",
            "New crops may require additional labour, seed and market access.",
            "Soil improvement cannot be guaranteed from rotation order alone.",
        ],
        "checks": [
            "Check local legume and cover-crop suitability.",
            "Review soil pH, organic matter and nutrient levels.",
            "Check water availability during the proposed crop period.",
            "Consider local pest and disease history.",
        ],
        "evidence": [
            "Saved crop history",
            "Other crops recorded in the farm profile",
            "Broad crop-family classification",
        ],
        "confidence": {
            "level": "Preliminary",
            "explanation": (
                "This is a candidate strategy based on the saved crop "
                "profile. Soil test results and local crop suitability "
                "are needed before making a field-level decision."
            ),
        },
    }


def _build_climate_resilience_rotation(farm_data: dict) -> dict:
    """Build a climate-resilience candidate for further screening."""
    sequence = farm_data["crop_sequence"]

    main_crop = (
        farm_data["main_crop"]
        or (sequence[0] if sequence else None)
    )

    next_crop = sequence[1] if len(sequence) > 1 else None

    if main_crop:
        proposed_sequence = (
            f"{main_crop} → locally climate-suitable alternative "
            "or crop phase"
        )

        if next_crop:
            proposed_sequence += f" → {next_crop}"

    else:
        proposed_sequence = (
            "Current crop → locally climate-suitable alternative "
            "→ next planned crop"
        )

    irrigation = farm_data["irrigation"] or "Not provided"
    priority = farm_data["priority"] or "Not provided"

    return {
        "number": "03",
        "strategy": "climate_resilience",
        "title": "Climate-Resilience Rotation",
        "sequence": proposed_sequence,
        "purpose": (
            "Explore crop sequences that can better fit local "
            "rainfall, temperature, growing seasons and water "
            "availability."
        ),
        "summary": (
            "This pathway needs climate-data screening before "
            "specific alternative crops can be ranked. "
            f"Recorded irrigation: {irrigation}. "
            f"Farmer priority: {priority}."
        ),
        "benefits": [
            "Can help identify crop options for different growing seasons.",
            "Can compare crop water requirements with available irrigation.",
            "Can help explore alternatives for periods of water stress.",
            "Can make climate-related trade-offs more visible.",
        ],
        "risks": [
            "Historical climate patterns do not guarantee future conditions.",
            "Satellite and gridded climate data may not represent "
            "exact field-level conditions.",
            "Crop suitability also depends on variety, soil and management.",
            "Changing crops may affect market access and farm income.",
        ],
        "checks": [
            "Evaluate local temperature and rainfall patterns.",
            "Check growing-season length and sowing windows.",
            "Compare crop water requirements with available water.",
            "Review local drought and excess-rainfall risks.",
        ],
        "evidence": [
            "Saved farm coordinates",
            "Saved irrigation method",
            "Saved sowing and harvest periods",
            "NASA climate observations: integration pending",
        ],
        "confidence": {
            "level": "Awaiting climate evidence",
            "explanation": (
                "Climate observations have not yet been retrieved. "
                "No climate suitability score or crop ranking is "
                "claimed at this stage."
            ),
        },
    }


def build_rotation_recommendations(farm: Any) -> dict:
    """
    Generate three rotation decision-support pathways
    using the saved farm profile.

    This initial version uses farm-profile information.
    Climate-data integration and locally validated crop rules
    will be added separately.
    """
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
            "sowing_season": farm_data["sowing_season"],
            "harvest_period": farm_data["harvest_period"],
            "current_sequence": farm_data["crop_sequence"],
            "priority": farm_data["priority"],
        },
        "profile_completeness": completeness,
        "comparison_status": (
            "Preliminary comparison. Climate data and local "
            "agronomic validation are not yet included."
        ),
        "scoring": {
            "available": False,
            "reason": (
                "Comparative scores will be introduced after "
                "climate evidence and crop-suitability rules "
                "have been integrated."
            ),
        },
        "pathways": pathways,
        "limitations": [
            "Crop-family classification is broad and may not cover "
            "every local crop or variety.",
            "Candidate sequences are not guaranteed recommendations.",
            "Local soil testing and agronomic guidance are required.",
            "Climate suitability has not yet been evaluated.",
        ],
    }
