"""Register ROOTWISE and M2/M3 models on one SQLAlchemy Base."""

from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.region import Region
from app.models.field import Field
from app.models.crop import Crop
from app.models.farm_rotation import FarmRotation
from app.models.climate_feature import ClimateFeature
from app.models.map_cell import MapCell
from app.models.scenario import Scenario
from app.models.layer_meta import LayerMeta

__all__ = [
    "Farm",
    "Farmer",
    "Region",
    "Field",
    "Crop",
    "FarmRotation",
    "ClimateFeature",
    "MapCell",
    "Scenario",
    "LayerMeta",
]
