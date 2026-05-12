import asyncio
import json
import re
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

IMDB_ID_PATTERN = re.compile(r"^(tt|nm)\d+$")
SUGGESTION_BASE_URL = "https://v3.sg.media-imdb.com/suggestion"
REQUEST_TIMEOUT_SECONDS = 8.0
MAX_CONCURRENT_REQUESTS = 8


def _entity_type_from_id(imdb_id: str) -> str:
    if imdb_id.startswith("tt"):
        return "title"
    if imdb_id.startswith("nm"):
        return "name"
    raise ValueError(f"Unsupported IMDb id: {imdb_id}")


def _suggestion_url_for_id(imdb_id: str) -> str:
    return f"{SUGGESTION_BASE_URL}/{imdb_id[0].lower()}/{imdb_id}.json"


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pick_item(payload: dict[str, Any], imdb_id: str) -> dict[str, Any] | None:
    candidates = payload.get("d")
    if not isinstance(candidates, list):
        return None

    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == imdb_id:
            return candidate
    return None


def _row_to_media(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "imdb_id": row["imdb_id"],
        "entity_type": row["entity_type"],
        "image_url": row["image_url"],
        "image_width": row["image_width"],
        "image_height": row["image_height"],
        "label": row["label"],
        "subtitle": row["subtitle"],
        "kind": row["kind"],
        "result_rank": row["result_rank"],
        "year": row["year"],
    }


async def _load_cached(db: AsyncSession, imdb_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
            SELECT
                imdb_id,
                entity_type,
                image_url,
                image_width,
                image_height,
                label,
                subtitle,
                kind,
                result_rank,
                year
            FROM imdb_media_cache
            WHERE imdb_id = :imdb_id
            """
        ),
        {"imdb_id": imdb_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    return _row_to_media(dict(row))


async def _upsert_cached(
    db: AsyncSession,
    imdb_id: str,
    payload: dict[str, Any],
    item: dict[str, Any] | None,
) -> None:
    image_data = item.get("i") if isinstance(item, dict) else None
    image_url = image_data.get("imageUrl") if isinstance(image_data, dict) else None
    image_width = _safe_int(image_data.get("width")) if isinstance(image_data, dict) else None
    image_height = _safe_int(image_data.get("height")) if isinstance(image_data, dict) else None

    await db.execute(
        text(
            """
            INSERT INTO imdb_media_cache (
                imdb_id,
                entity_type,
                image_url,
                image_width,
                image_height,
                label,
                subtitle,
                kind,
                result_rank,
                year,
                raw_item,
                raw_response,
                fetched_at,
                updated_at
            )
            VALUES (
                :imdb_id,
                :entity_type,
                :image_url,
                :image_width,
                :image_height,
                :label,
                :subtitle,
                :kind,
                :result_rank,
                :year,
                :raw_item,
                :raw_response,
                NOW(),
                NOW()
            )
            ON CONFLICT (imdb_id)
            DO UPDATE SET
                entity_type = EXCLUDED.entity_type,
                image_url = EXCLUDED.image_url,
                image_width = EXCLUDED.image_width,
                image_height = EXCLUDED.image_height,
                label = EXCLUDED.label,
                subtitle = EXCLUDED.subtitle,
                kind = EXCLUDED.kind,
                result_rank = EXCLUDED.result_rank,
                year = EXCLUDED.year,
                raw_item = EXCLUDED.raw_item,
                raw_response = EXCLUDED.raw_response,
                updated_at = NOW()
            """
        ),
        {
            "imdb_id": imdb_id,
            "entity_type": _entity_type_from_id(imdb_id),
            "image_url": image_url,
            "image_width": image_width,
            "image_height": image_height,
            "label": item.get("l") if isinstance(item, dict) else None,
            "subtitle": item.get("s") if isinstance(item, dict) else None,
            "kind": item.get("qid") if isinstance(item, dict) else None,
            "result_rank": _safe_int(item.get("rank")) if isinstance(item, dict) else None,
            "year": _safe_int(item.get("y")) if isinstance(item, dict) else None,
            "raw_item": json.dumps(item, ensure_ascii=False) if item is not None else None,
            "raw_response": json.dumps(payload, ensure_ascii=False),
        },
    )


async def _fetch_payload(client: httpx.AsyncClient, imdb_id: str) -> dict[str, Any] | None:
    try:
        response = await client.get(_suggestion_url_for_id(imdb_id))
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None
    return payload


async def get_media_map(db: AsyncSession, imdb_ids: list[str]) -> dict[str, dict[str, Any] | None]:
    output: dict[str, dict[str, Any] | None] = {}
    missing: list[str] = []
    wrote_cache = False

    for imdb_id in dict.fromkeys(imdb_ids):
        if not IMDB_ID_PATTERN.match(imdb_id):
            output[imdb_id] = None
            continue

        cached = await _load_cached(db, imdb_id)
        if cached:
            output[imdb_id] = cached
            continue

        missing.append(imdb_id)

    if not missing:
        return output

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        async def fetch_one(imdb_id: str) -> tuple[str, dict[str, Any] | None]:
            async with semaphore:
                payload = await _fetch_payload(client, imdb_id)
                return imdb_id, payload

        fetched_payloads = await asyncio.gather(*(fetch_one(imdb_id) for imdb_id in missing))

    for imdb_id, payload in fetched_payloads:
        if payload is None:
            output[imdb_id] = None
            continue

        item = _pick_item(payload, imdb_id)
        await _upsert_cached(db, imdb_id, payload, item)
        wrote_cache = True

        if item is None:
            output[imdb_id] = None
            continue

        output[imdb_id] = {
            "imdb_id": imdb_id,
            "entity_type": _entity_type_from_id(imdb_id),
            "image_url": item.get("i", {}).get("imageUrl") if isinstance(item.get("i"), dict) else None,
            "image_width": _safe_int(item.get("i", {}).get("width")) if isinstance(item.get("i"), dict) else None,
            "image_height": _safe_int(item.get("i", {}).get("height")) if isinstance(item.get("i"), dict) else None,
            "label": item.get("l"),
            "subtitle": item.get("s"),
            "kind": item.get("qid"),
            "result_rank": _safe_int(item.get("rank")),
            "year": _safe_int(item.get("y")),
        }

    if wrote_cache:
        await db.commit()

    return output
