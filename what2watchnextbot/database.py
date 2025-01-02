import sqlalchemy.ext.asyncio as async_sa

engine = async_sa.create_async_engine(
    "postgresql+psycopg://localhost/what2watchnextbot"
)
session_factory = async_sa.async_sessionmaker(bind=engine)
