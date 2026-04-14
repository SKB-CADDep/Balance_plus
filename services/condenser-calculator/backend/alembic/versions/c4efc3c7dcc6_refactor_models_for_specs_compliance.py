"""Refactor models for specs compliance

Revision ID: c4efc3c7dcc6
Revises: d2b27e2a603a
Create Date: 2026-04-14 15:02:24.765168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4efc3c7dcc6'
down_revision: Union[str, Sequence[str], None] = 'd2b27e2a603a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Update Materials
    op.add_column('materials', sa.Column('material_uuid', sa.String(), nullable=False))
    op.create_index(op.f('ix_materials_material_uuid'), 'materials', ['material_uuid'], unique=True)
    op.alter_column('materials', 'thermal_properties', new_column_name='thermal_conductivity_points')

    # 2. Update Condensers
    op.add_column('condensers', sa.Column('project_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Revert Condensers
    op.drop_column('condensers', 'project_id')

    # 2. Revert Materials
    op.alter_column('materials', 'thermal_conductivity_points', new_column_name='thermal_properties')
    op.drop_index(op.f('ix_materials_material_uuid'), table_name='materials')
    op.drop_column('materials', 'material_uuid')
