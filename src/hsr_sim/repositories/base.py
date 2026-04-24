from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from hsr_sim.logger import get_logger
from hsr_sim.models.db.base import Base

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
        return obj

    def add_all(self, objs: list[ModelType]) -> list[ModelType]:
        self.db.add_all(objs)
        return objs

    def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        return obj

    def list_by_filters(self, **filters: Any) -> list[ModelType]:
        return self.db.query(self.model).filter_by(**filters).all()

    def get_one_by_filters(self, **filters: Any) -> ModelType | None:
        return self.db.query(self.model).filter_by(**filters).one_or_none()

    def update(self, id: int, **kwargs: Any) -> ModelType | None:
        obj = self.get(id)
        if obj is None:
            return None
        for field, value in kwargs.items():
            setattr(obj, field, value)
        return obj

    def count(self) -> int:
        return self.db.query(self.model).count()

    def exists(self, id: int) -> bool:
        return self.get(id) is not None

    def delete(self, id: int) -> None:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
        else:
            logger.warning(
                f"{self.model.__name__} with id {id} not found for deletion."
            )

    # 不提供 update，由调用方直接修改从 get 返回的托管对象
