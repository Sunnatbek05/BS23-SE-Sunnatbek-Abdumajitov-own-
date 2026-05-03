from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Establish local SQLite database connection URL
DATABASE_URL = "sqlite+aiosqlite:///./kunlik_hisobot.db"

# Initialize async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Bootstrap database and synchronize metadata
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)