from pydantic import BaseModel


class CharacterIdentityComponent(BaseModel):
    config_id: int
    config_name: str
    version: str
