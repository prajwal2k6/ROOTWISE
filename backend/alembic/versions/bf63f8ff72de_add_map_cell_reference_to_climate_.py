
"""add map cell reference to climate features

Revision ID: bf63f8ff72de
Revises: f9f39d68fa8f
Create Date: 2026-11-14 17:36:32.044767
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision: str = 'bf63f8ff72de'
down_revision: Union[str, Sequence[str], None] = 'f9f39d68fa8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add map cell reference to climate features."""

    op.add_column(
        'climate_features',
        sa.Column('map_cell_id', sa.Integer(), nullable=True)
    )

    op.create_index(
        op.f('ix_climate_features_map_cell_id'),
        'climate_features',
        ['map_cell_id'],
        unique=False
    )

    op.create_foreign_key(
        'fk_climate_features_map_cell_id',
        'climate_features',
        'map_cells',
        ['map_cell_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove map cell reference from climate features."""

    op.drop_constraint(
        'fk_climate_features_map_cell_id',
        'climate_features',
        type_='foreignkey'
    )

    op.drop_index(
        op.f('ix_climate_features_map_cell_id'),
        table_name='climate_features'
    )

    op.drop_column(
        'climate_features',
        'map_cell_id'
    )
