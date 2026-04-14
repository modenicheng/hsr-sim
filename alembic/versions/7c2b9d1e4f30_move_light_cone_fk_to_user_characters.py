"""move light cone fk to user_characters

Revision ID: 7c2b9d1e4f30
Revises: b9f3c8e4a1d2
Create Date: 2026-04-14 21:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c2b9d1e4f30"
down_revision: Union[str, Sequence[str], None] = "b9f3c8e4a1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user_characters", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("equipped_light_cone_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_user_characters_equipped_light_cone_id",
            "user_light_cones",
            ["equipped_light_cone_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "uq_user_characters_equipped_light_cone_id", ["equipped_light_cone_id"]
        )

    op.execute(
        sa.text(
            """
            UPDATE user_characters
            SET equipped_light_cone_id = (
                SELECT ulc.id
                FROM user_light_cones AS ulc
                WHERE ulc.equipped_by = user_characters.id
            )
            WHERE EXISTS (
                SELECT 1
                FROM user_light_cones AS ulc
                WHERE ulc.equipped_by = user_characters.id
            )
            """
        )
    )

    with op.batch_alter_table("user_light_cones", recreate="always") as batch_op:
        batch_op.drop_column("equipped_by")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user_light_cones", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("equipped_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_user_light_cones_equipped_by",
            "user_characters",
            ["equipped_by"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_unique_constraint("uq_user_light_cones_equipped_by", ["equipped_by"])

    op.execute(
        sa.text(
            """
            UPDATE user_light_cones
            SET equipped_by = (
                SELECT uc.id
                FROM user_characters AS uc
                WHERE uc.equipped_light_cone_id = user_light_cones.id
            )
            WHERE EXISTS (
                SELECT 1
                FROM user_characters AS uc
                WHERE uc.equipped_light_cone_id = user_light_cones.id
            )
            """
        )
    )

    with op.batch_alter_table("user_characters", recreate="always") as batch_op:
        batch_op.drop_column("equipped_light_cone_id")
