"""create imdb raw tables

Revision ID: 03b58f4b3c79
Revises: 
Create Date: 2026-04-24 21:17:18.668540

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '03b58f4b3c79'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE name_basics (
            nconst TEXT PRIMARY KEY,
            primaryName TEXT,
            birthYear TEXT,
            deathYear TEXT,
            primaryProfession TEXT,
            knownForTitles TEXT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_basics (
            tconst TEXT PRIMARY KEY,
            titleType TEXT,
            primaryTitle TEXT,
            originalTitle TEXT,
            isAdult SMALLINT,
            startYear TEXT,
            endYear TEXT,
            runtimeMinutes TEXT,
            genres TEXT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_akas (
            titleId TEXT,
            ordering INTEGER,
            title TEXT,
            region TEXT,
            language TEXT,
            types TEXT,
            attributes TEXT,
            isOriginalTitle SMALLINT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_crew (
            tconst TEXT PRIMARY KEY,
            directors TEXT,
            writers TEXT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_episode (
            tconst TEXT PRIMARY KEY,
            parentTconst TEXT,
            seasonNumber TEXT,
            episodeNumber TEXT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_principals (
            tconst TEXT,
            ordering INTEGER,
            nconst TEXT,
            category TEXT,
            job TEXT,
            characters TEXT
        );
        """
    )

    op.execute(
        """
        CREATE TABLE title_ratings (
            tconst TEXT PRIMARY KEY,
            averageRating FLOAT,
            numVotes INTEGER
        );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS title_ratings;")
    op.execute("DROP TABLE IF EXISTS title_principals;")
    op.execute("DROP TABLE IF EXISTS title_episode;")
    op.execute("DROP TABLE IF EXISTS title_crew;")
    op.execute("DROP TABLE IF EXISTS title_akas;")
    op.execute("DROP TABLE IF EXISTS title_basics;")
    op.execute("DROP TABLE IF EXISTS name_basics;")
