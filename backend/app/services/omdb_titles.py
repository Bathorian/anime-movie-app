import json
import os
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

OMDB_BASE_URL = os.getenv("OMDB_BASE_URL", "https://www.omdbapi.com/")
OMDB_API_KEY = os.getenv("OMDB_API_KEY") or "thewdb"
REQUEST_TIMEOUT_SECONDS = 8.0


def _clean_omdb_value(value: Any) -> str | None:
    if value is None:
        return None
    string_value = str(value).strip()
    if not string_value or string_value == "N/A":
        return None
    return string_value


async def _load_cached_plot(db: AsyncSession, imdb_id: str) -> tuple[str | None, str | None] | None:
    result = await db.execute(
        text(
            """
            SELECT plot, provider
            FROM omdb_title_cache
            WHERE imdb_id = :imdb_id
            """
        ),
        {"imdb_id": imdb_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    return row.get("plot"), row.get("provider")


async def _save_omdb_payload(db: AsyncSession, imdb_id: str, payload: dict[str, Any]) -> tuple[str | None, str | None]:
    plot = _clean_omdb_value(payload.get("Plot"))
    provider = "omdb"

    await db.execute(
        text(
            """
            INSERT INTO omdb_title_cache (
                imdb_id,
                provider,
                title,
                year,
                rated,
                released,
                runtime,
                genre,
                director,
                writer,
                actors,
                language,
                country,
                awards,
                plot,
                metascore,
                imdb_rating,
                imdb_votes,
                response_status,
                error_message,
                raw_response,
                fetched_at,
                updated_at
            )
            VALUES (
                :imdb_id,
                :provider,
                :title,
                :year,
                :rated,
                :released,
                :runtime,
                :genre,
                :director,
                :writer,
                :actors,
                :language,
                :country,
                :awards,
                :plot,
                :metascore,
                :imdb_rating,
                :imdb_votes,
                :response_status,
                :error_message,
                :raw_response,
                NOW(),
                NOW()
            )
            ON CONFLICT (imdb_id)
            DO UPDATE SET
                provider = EXCLUDED.provider,
                title = EXCLUDED.title,
                year = EXCLUDED.year,
                rated = EXCLUDED.rated,
                released = EXCLUDED.released,
                runtime = EXCLUDED.runtime,
                genre = EXCLUDED.genre,
                director = EXCLUDED.director,
                writer = EXCLUDED.writer,
                actors = EXCLUDED.actors,
                language = EXCLUDED.language,
                country = EXCLUDED.country,
                awards = EXCLUDED.awards,
                plot = EXCLUDED.plot,
                metascore = EXCLUDED.metascore,
                imdb_rating = EXCLUDED.imdb_rating,
                imdb_votes = EXCLUDED.imdb_votes,
                response_status = EXCLUDED.response_status,
                error_message = EXCLUDED.error_message,
                raw_response = EXCLUDED.raw_response,
                updated_at = NOW()
            """
        ),
        {
            "imdb_id": imdb_id,
            "provider": provider,
            "title": _clean_omdb_value(payload.get("Title")),
            "year": _clean_omdb_value(payload.get("Year")),
            "rated": _clean_omdb_value(payload.get("Rated")),
            "released": _clean_omdb_value(payload.get("Released")),
            "runtime": _clean_omdb_value(payload.get("Runtime")),
            "genre": _clean_omdb_value(payload.get("Genre")),
            "director": _clean_omdb_value(payload.get("Director")),
            "writer": _clean_omdb_value(payload.get("Writer")),
            "actors": _clean_omdb_value(payload.get("Actors")),
            "language": _clean_omdb_value(payload.get("Language")),
            "country": _clean_omdb_value(payload.get("Country")),
            "awards": _clean_omdb_value(payload.get("Awards")),
            "plot": plot,
            "metascore": _clean_omdb_value(payload.get("Metascore")),
            "imdb_rating": _clean_omdb_value(payload.get("imdbRating")),
            "imdb_votes": _clean_omdb_value(payload.get("imdbVotes")),
            "response_status": _clean_omdb_value(payload.get("Response")),
            "error_message": _clean_omdb_value(payload.get("Error")),
            "raw_response": json.dumps(payload, ensure_ascii=False),
        },
    )
    await db.commit()

    return plot, provider


async def get_title_plot(db: AsyncSession, imdb_id: str) -> tuple[str | None, str | None]:
    cached = await _load_cached_plot(db, imdb_id)
    if cached is not None:
        return cached

    if not OMDB_API_KEY:
        return None, None

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(
                OMDB_BASE_URL,
                params={
                    "apikey": OMDB_API_KEY,
                    "i": imdb_id,
                    "plot": "full",
                    "r": "json",
                },
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None, None

    if not isinstance(payload, dict):
        return None, None

    return await _save_omdb_payload(db, imdb_id, payload)
