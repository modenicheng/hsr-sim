from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.hsr_sim.core.config import PROJECT_ROOT

# 数据库文件放在 data/ 目录
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'hsr.db'}"

engine = create_engine(DATABASE_URL,
                       echo=False,
                       connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
