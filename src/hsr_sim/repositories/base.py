from typing import TypeVar, Generic
from sqlalchemy.orm import Session
from src.hsr_sim.models.db.base import Base
from src.hsr_sim.logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> ModelType | None:
        return self.db.get(self.model, id)

    def get_all(self) -> list[ModelType]:
        return self.db.query(self.model).all()

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.db.merge(obj)
        self.db.commit()
        return obj

    def delete(self, id: int) -> None:
        obj: ModelType | None = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return
        logger.warning(
            f"ORM Object {self.model.__name__} with id {id} not found for deletion. Skipping."
        )
