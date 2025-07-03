import asyncio

from dotenv import load_dotenv
from loguru import logger

from app import logging
from app.config import Config
from app.core.services import title as title_service
from app.database import init_async


async def main() -> None:
    load_dotenv()

    config = Config.from_unprefixed_env()

    logging.init(config.logging)
    engine, session_factory = init_async(config.db)

    logger.info("Importing titles from IMDB")
    try:
        async with session_factory() as session:
            await title_service.refresh_from_imdb(session)
            await session.commit()
        logger.info("Successfully imported titles from IMDB")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
