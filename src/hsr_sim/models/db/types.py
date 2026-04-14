# src/hsr_sim/models/db/types.py
import orjson
from sqlalchemy import TypeDecorator, TEXT


class JSONText(TypeDecorator):
    """将 Python 的 dict/list 自动序列化为 TEXT 存储在数据库中"""
    impl = TEXT  # 告诉 SQLAlchemy，底层使用 TEXT 列

    def process_bind_param(self, value, dialect):
        """Python -> Database"""
        if value is not None:
            return orjson.dumps(value)  # ensure_ascii=False 支持中文
        return value

    def process_result_value(self, value, dialect):
        """Database -> Python"""
        if value is not None:
            return orjson.loads(value)
        return value
