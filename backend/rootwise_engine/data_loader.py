from functools import lru_cache
from importlib.resources import files
import yaml
from .models import Crop

@lru_cache(maxsize=1)
def load_crops() -> list[Crop]:
    data=yaml.safe_load(files("rootwise_engine").joinpath("data/crops.yaml").read_text(encoding="utf-8"))
    return [Crop.model_validate(x) for x in data["crops"]]

def _load(name):
    return yaml.safe_load(files("rootwise_engine").joinpath(f"data/{name}.yaml").read_text(encoding="utf-8"))

def load_criteria(): return _load("criteria")
def load_glossary(): return _load("glossary")


def load_variety_profiles(): return _load('variety_profiles')
