"""update relationships

Revision ID: 4e1465a6cd01
Revises: 405808fdbf19
Create Date: 2026-04-14 19:45:11.389220

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4e1465a6cd01"
down_revision: Union[str, Sequence[str], None] = "405808fdbf19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user_characters", recreate="always") as batch_op:
        batch_op.drop_column("equipped_light_cone_id")
    with op.batch_alter_table(
        "user_light_cones", recreate="always"
    ) as batch_op:
        batch_op.add_column(
            sa.Column("equipped_by", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_user_light_cones_equipped_by",
            "user_characters",
            ["equipped_by"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table(
        "user_light_cones", recreate="always"
    ) as batch_op:
        batch_op.drop_column("equipped_by")
    with op.batch_alter_table("user_characters", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("equipped_light_cone_id", sa.INTEGER(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_user_characters_equipped_light_cone_id",
            "user_light_cones",
            ["equipped_light_cone_id"],
            ["id"],
            ondelete="SET NULL",
        )
