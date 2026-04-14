# ecs/components/equipment.py
from pydantic import BaseModel


class EquippedRelicsComponent(BaseModel):
    """角色当前装备的遗器实例ID"""
    head: int | None = None
    hands: int | None = None
    torso: int | None = None
    feet: int | None = None
    planar_sphere: int | None = None
    link_rope: int | None = None
