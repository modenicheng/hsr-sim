"""make light cone equipped_by unique

Revision ID: b9f3c8e4a1d2
Revises: 3dab4cf2cfb7
Create Date: 2026-04-14 20:10:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b9f3c8e4a1d2"
down_revision: Union[str, Sequence[str], None] = "3dab4cf2cfb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table(
        "user_light_cones", recreate="always"
    ) as batch_op:
        batch_op.create_unique_constraint(
            "uq_user_light_cones_equipped_by", ["equipped_by"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table(
        "user_light_cones", recreate="always"
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_user_light_cones_equipped_by", type_="unique"
        )
