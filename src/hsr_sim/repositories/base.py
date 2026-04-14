from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session
from src.hsr_sim.models.db.base import Base
from src.hsr_sim.logger import get_logger

logger = get_logger(__name__)
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def get_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        return obj

    def add_all(self, objs: List[ModelType]) -> List[ModelType]:
        self.db.add_all(objs)
        return objs

    def delete(self, id: int) -> None:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
        else:
            logger.warning(f"{self.model.__name__} with id {id} not found for deletion.")

    # 不提供 update，由调用方直接修改从 get 返回的托管对象