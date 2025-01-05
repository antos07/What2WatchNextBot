import aiogram
import click
import dotenv
import pydantic
from loguru import logger

import alembic.command  # noqa: I001
import alembic.config
from what2watchnextbot import logging
from what2watchnextbot.dispatcher import create_dispatcher
from what2watchnextbot.settings import get_settings


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    help="Log level.",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    show_default=True,
)
@click.option("--env", is_flag=True, help="Load .env file.", show_default=True)
@click.pass_context
def cli(ctx, log_level, env):
    """A CLI to manage What2WatchNextBot"""
    logging.configure(level=log_level)

    if env:
        dotenv.load_dotenv()
        logger.info("Loaded .env file.")

    ctx.obj = ctx.ensure_object(dict)

    try:
        ctx.obj["settings"] = get_settings()
    except pydantic.ValidationError as e:
        logger.error(f"Failed to load settings from environment variables.\n{e}")
        ctx.abort()


@cli.group()
@click.option(
    "-c",
    "--config-file",
    type=click.Path(exists=True, dir_okay=False),
    default="alembic.ini",
    show_default=True,
    help="Path to alembic configuration file.",
)
@click.pass_context
def db(ctx, config_file):
    """Manage the database. Mostly shortcuts for Alembic commands."""

    ctx.obj["config"] = alembic.config.Config(config_file)


@db.command()
@click.argument("message")
@click.pass_context
def revision(ctx, message: str):
    """Auto-generate a new revision.

    MESSAGE - Message string to use with 'revision'.
    """

    alembic.command.revision(
        config=ctx.obj["config"],
        message=message,
        autogenerate=True,
    )


@db.command()
@click.argument("revision", default="head")
@click.pass_context
def upgrade(ctx, revision):
    """Upgrade the database to a revision.

    REVISION - Revision identifier. Default is head.
    """
    alembic.command.upgrade(config=ctx.obj["config"], revision=revision)


@db.command()
@click.argument("revision", default="-1")
@click.pass_context
def downgrade(ctx, revision):
    """Downgrade the database to a revision.

    REVISION - Revision identifier. Default is -1.
    """
    alembic.command.downgrade(config=ctx.obj["config"], revision=revision)


@cli.group()
def run():
    """Run the bot"""
    pass


@run.command()
@click.pass_context
def polling(ctx):
    """Run the bot in the polling mode"""

    bot = aiogram.Bot(ctx.obj["settings"].BOT_TOKEN)
    dispatcher = create_dispatcher()
    dispatcher.run_polling(bot)
