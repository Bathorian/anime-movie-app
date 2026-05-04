from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/search")
async def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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
        LIMIT :limit OFFSET :offset
    """), {"q": f"%{q}%", "limit": limit, "offset": offset})

    rows = result.mappings().all()
    return {"results": [dict(r) for r in rows], "page": page}


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

    # Get top cast
    cast = await db.execute(text("""
        SELECT
            tp.category,
            tp.characters,
            nb.primaryName
        FROM title_principals tp
        JOIN name_basics nb ON tp.nconst = nb.nconst
        WHERE tp.tconst = :tconst
        ORDER BY tp.ordering
        LIMIT 10
    """), {"tconst": tconst})

    return {
        **dict(movie),
        "cast": [dict(c) for c in cast.mappings().all()]
    }
