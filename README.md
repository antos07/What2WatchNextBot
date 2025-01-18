# What2WatchNextBot

A Telegram bot to match you with a title you will watch tonight.

**[Try It](https://t.me/what2watchnextbot)**

## How does it work?

It's powered by the official open [dataset](https://developer.imdb.com/non-commercial-datasets/)
of IMDB titles, that includes 450k+ movies and series.

The original idea was to create a "dating app" for movies where a user can click "no" until they
find something they like.
But this would also require some simple filtering to make suggestions really useful.
And that's how this bot was born.

Users get some of the most useful filters from IMDB's advanced search (e.g., genres or rating),
and at the same time, they no longer need to scroll through a huge list of titles the search finds.
Instead, they receive a suggestion, then watch it or decide what to do with this title in the future
(e.g., it won't be suggested anymore, if the user has already watched it).

## Implementation details

The bot is implemented in Python 3.13, uses [Aiogram](https://github.com/aiogram/aiogram) framework
and, as an experiment, mostly relies on the new
[Scenes](https://docs.aiogram.dev/en/stable/dispatcher/finite_state_machine/scene.html) feature.
All the database stuff (including filtering) uses 
[SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/index.html)
and [PostgreSQL](https://www.postgresql.org/) (however, it may actually work with some other databases
as well, due to SQLAlchemy).
It also uses [Redis](https://redis.io) for state management (that's an internal thing of Aiogram)
and [Pandas](https://pandas.pydata.org/) to import the dataset.

## Installation

You will need Python 3.13, modern PostgreSQL, Redis and [Poetry](https://python-poetry.org/docs/)
installed.

Clone the repository (but you probably already knew this part)

      git clone https://github.com/antos07/What2WatchNextBot.git

And now let Poetry do its work

      poetry install

After that, the installation is completed, and you can run the CLI using `python -m what2watchnextbot`
or simply `what2watchnextbot` (you may have to use `poetry run` or `poetry shell` though).
