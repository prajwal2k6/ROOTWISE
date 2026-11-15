
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.field import Field
from app.models.scenario import Scenario


class FieldNotFoundError(Exception):
    pass


class ScenarioNotFoundError(Exception):
    pass


def create_simulation(
    db: Session,
    field_id: int,
    title: str,
    description: str | None,
    input_parameters: dict,
) -> Scenario:

    field = db.get(Field, field_id)

    if field is None:
        raise FieldNotFoundError("Field not found")

    scenario = Scenario(
        field_id=field.id,
        farmer_id=field.farmer_id,
        title=title,
        description=description,
        input_parameters=input_parameters,
        result=None,
        status="pending",
    )

    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return scenario


def get_simulation(
    db: Session,
    scenario_id: int,
) -> Scenario:

    scenario = db.get(Scenario, scenario_id)

    if scenario is None:
        raise ScenarioNotFoundError("Simulation not found")

    return scenario


def get_field_simulations(
    db: Session,
    field_id: int,
) -> list[Scenario]:

    if db.get(Field, field_id) is None:
        raise FieldNotFoundError("Field not found")

    query = (
        select(Scenario)
        .where(Scenario.field_id == field_id)
        .order_by(Scenario.created_at.desc())
    )

    return db.scalars(query).all()
