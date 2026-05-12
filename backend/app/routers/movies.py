import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.imdb_images import get_media_map
from app.services.omdb_titles import get_title_plot

router = APIRouter(prefix="/movies", tags=["movies"])


def title_imdb_url(tconst: str) -> str:
    return f"https://www.imdb.com/title/{tconst}/"


def name_imdb_url(nconst: str) -> str:
    return f"https://www.imdb.com/name/{nconst}/"


def clean_imdb_value(value: str | None) -> str | None:
    if value is None:
        return None
    if value == "\\N":
        return None
    return value


def normalize_characters(raw: str | None) -> str | None:
    cleaned = clean_imdb_value(raw)
    if not cleaned:
        return None

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned

    if isinstance(parsed, list):
        values = [str(item).strip() for item in parsed if str(item).strip()]
        return ", ".join(values) if values else None

    return str(parsed)

@router.get("/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(text("""
        SELECT
            tb.tconst,
            tb.primaryTitle,
            tb.startYear,
            tb.genres,
            tb.runtimeMinutes,
            tb.titleType,
            tr.averageRating,
            tr.numVotes
        FROM title_basics tb
        LEFT JOIN title_ratings tr ON tb.tconst = tr.tconst
        WHERE tb.primaryTitle ILIKE :q
          AND tb.titleType IN ('movie', 'tvSeries', 'short', 'tvMovie')
          AND tb.startYear != '\\N'
        ORDER BY tr.numVotes DESC NULLS LAST
        LIMIT :limit_plus_one OFFSET :offset
    """), {"q": f"%{q}%", "limit_plus_one": limit + 1, "offset": offset})

    rows = result.mappings().all()
    has_more = len(rows) > limit
    movies = [dict(r) for r in rows[:limit]]

    media_map = await get_media_map(db, [movie["tconst"] for movie in movies])
    for movie in movies:
        media = media_map.get(movie["tconst"])
        movie["posterurl"] = media["image_url"] if media else None
        movie["imdburl"] = title_imdb_url(movie["tconst"])

    return {
        "results": movies,
        "page": page,
        "limit": limit,
        "has_more": has_more,
    }


@router.get("/{tconst}")
async def get_movie(tconst: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            tb.tconst,
            tb.primaryTitle,
            tb.originalTitle,
            tb.startYear,
            tb.endYear,
            tb.genres,
            tb.runtimeMinutes,
            tb.titleType,
            tb.isAdult,
            tr.averageRating,
            tr.numVotes
        FROM title_basics tb
        LEFT JOIN title_ratings tr ON tb.tconst = tr.tconst
        WHERE tb.tconst = :tconst
    """), {"tconst": tconst})

    movie = result.mappings().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Get all cast/principals rows for this title.
    cast = await db.execute(text("""
        SELECT
            tp.nconst,
            tp.ordering,
            tp.category,
            tp.job,
            tp.characters,
            nb.primaryName
        FROM title_principals tp
        LEFT JOIN name_basics nb ON tp.nconst = nb.nconst
        WHERE tp.tconst = :tconst
        ORDER BY tp.ordering
    """), {"tconst": tconst})

    directors = await db.execute(text("""
        SELECT
            d.ord AS ordering,
            d.nconst,
            nb.primaryName
        FROM title_crew tc
        CROSS JOIN LATERAL unnest(string_to_array(tc.directors, ',')) WITH ORDINALITY AS d(nconst, ord)
        LEFT JOIN name_basics nb ON nb.nconst = d.nconst
        WHERE tc.tconst = :tconst
        ORDER BY d.ord
    """), {"tconst": tconst})

    writers = await db.execute(text("""
        SELECT
            w.ord AS ordering,
            w.nconst,
            nb.primaryName
        FROM title_crew tc
        CROSS JOIN LATERAL unnest(string_to_array(tc.writers, ',')) WITH ORDINALITY AS w(nconst, ord)
        LEFT JOIN name_basics nb ON nb.nconst = w.nconst
        WHERE tc.tconst = :tconst
        ORDER BY w.ord
    """), {"tconst": tconst})

    akas = await db.execute(text("""
        SELECT
            ordering,
            title,
            region,
            language,
            types,
            attributes,
            isOriginalTitle
        FROM title_akas
        WHERE titleId = :tconst
        ORDER BY ordering
    """), {"tconst": tconst})

    cast_rows = [dict(c) for c in cast.mappings().all()]
    directors_rows = [dict(c) for c in directors.mappings().all()]
    writers_rows = [dict(c) for c in writers.mappings().all()]
    akas_rows = [dict(a) for a in akas.mappings().all()]

    media_ids = [tconst]
    media_ids.extend(
        row["nconst"]
        for row in cast_rows
        if isinstance(row.get("nconst"), str) and row["nconst"].startswith("nm")
    )
    media_ids.extend(
        row["nconst"]
        for row in directors_rows
        if isinstance(row.get("nconst"), str) and row["nconst"].startswith("nm")
    )
    media_ids.extend(
        row["nconst"]
        for row in writers_rows
        if isinstance(row.get("nconst"), str) and row["nconst"].startswith("nm")
    )
    media_map = await get_media_map(db, media_ids)

    cast_with_images = []
    for row in cast_rows:
        nconst = row.get("nconst")
        media = media_map.get(nconst) if isinstance(nconst, str) else None
        cast_with_images.append({
            **row,
            "job": clean_imdb_value(row.get("job")),
            "characters": normalize_characters(row.get("characters")),
            "primaryname": row.get("primaryname") or nconst,
            "profileurl": media["image_url"] if media else None,
            "imdburl": name_imdb_url(nconst) if isinstance(nconst, str) else None,
        })

    def map_crew_rows(rows: list[dict]) -> list[dict]:
        crew_members = []
        for row in rows:
            nconst = row.get("nconst")
            media = media_map.get(nconst) if isinstance(nconst, str) else None
            crew_members.append({
                **row,
                "primaryname": row.get("primaryname") or nconst,
                "profileurl": media["image_url"] if media else None,
                "imdburl": name_imdb_url(nconst) if isinstance(nconst, str) else None,
            })
        return crew_members

    directors_with_images = map_crew_rows(directors_rows)
    writers_with_images = map_crew_rows(writers_rows)

    movie_media = media_map.get(tconst)
    plot, plot_source = await get_title_plot(db, tconst)

    normalized_akas = [
        {
            **row,
            "region": clean_imdb_value(row.get("region")),
            "language": clean_imdb_value(row.get("language")),
            "types": clean_imdb_value(row.get("types")),
            "attributes": clean_imdb_value(row.get("attributes")),
        }
        for row in akas_rows
    ]

    return {
        **dict(movie),
        "posterurl": movie_media["image_url"] if movie_media else None,
        "imdburl": title_imdb_url(tconst),
        "description": plot,
        "description_source": plot_source,
        "cast": cast_with_images,
        "cast_count": len(cast_with_images),
        "crew": {
            "directors": directors_with_images,
            "writers": writers_with_images,
        },
        "akas": normalized_akas,
        "akas_count": len(normalized_akas),
    }
