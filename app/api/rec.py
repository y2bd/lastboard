from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

import aiohttp
from sanic.exceptions import ServerError
from sanic.log import logger

from app.util.cache import cache_or_run
from app.util.slug import Slug
from app.util.unaccent import unaccent
from app.util.unartist import unartist
from settings import DEFAULT_REC_USER, REC_API_BASE_URL


@dataclass
class Release:
    title: str
    artist: str
    page_relative_url: str

    def __str__(self):
        return f"{self.artist} - {self.title}"


async def get_recent_queue(
    client: aiohttp.ClientSession, user: str = DEFAULT_REC_USER, limit=40
) -> Iterable[Release]:
    (response_dict, _) = await cache_or_run(
        "releases", _get_recent_queue_request(client, user, limit)
    )

    data: list = response_dict.get("data", [])

    logger.debug(f"Fetched {len(data)} releases for user {user}")

    return (
        Release(
            title=release.get("title"),
            artist=_get_primary_artist(release),
            page_relative_url=release.get("uri"),
        )
        for release in data
    )


async def _get_recent_queue_request(
    client: aiohttp.ClientSession, user: str, limit=40
) -> dict:
    async with client.get(
        urljoin(REC_API_BASE_URL, f"users/{user}/releases"),
        params={"limit": limit, "sortBy": "date-added-desc"},
    ) as response:
        logger.debug(f"Fetched recent queue for user {user}")
        return await response.json()


def _get_primary_artist(release_data) -> str:
    return release_data.get("artists")[0].get("name")


async def search_artist(client: aiohttp.ClientSession, artist: str) -> str | None:
    artist = _normalize_artist_name(artist)

    async with client.post(
        urljoin(REC_API_BASE_URL, "search/v2"),
        json={
            "query": artist,
            "entities": {
                "artists": ["people", "groups", "orchestras", "choirs", "other"]
            },
            "limit": 10,
        },
    ) as response:
        response_body = await response.json()
        if response_body["success"]:
            releases = sorted(
                response_body["data"],
                key=lambda r: r.get("popularity", 0),
                reverse=True,
            )

            logger.debug(releases)
            return releases[0]["slug"]
        else:
            return None


async def search_release(client: aiohttp.ClientSession, slug: Slug) -> Release | None:
    artist = _normalize_artist_name(slug.artist)
    title = _normalize_release_title(slug.title)

    (response_body, _) = await cache_or_run(
        f"search-release-{artist}-{title}",
        _search_release_request(client, artist, title),
        # 3 days, releases should not change frequently
        cache_time_seconds=60 * 60 * 72,
    )

    releases = sorted(
        response_body["data"],
        key=_rank_release,
        reverse=True,
    )

    release = releases[0] if releases else None
    if release is None:
        return None

    try:
        return Release(
            title=release["title"],
            artist=_get_primary_artist(release),
            page_relative_url=release["uri"],
        )
    except Exception as e:
        logger.exception(e)
        raise ServerError("Failed to parse release data")


def _rank_release(release_data: dict) -> int:
    popularity: int = release_data.get("popularity", 0)
    release_type: int = release_data.get("type", 0)

    # popularity is increasing, the higher the better
    # release type has album as the lowest and more specifics as higher numbers, so punish higher numbers
    return popularity - release_type


async def _search_release_request(
    client: aiohttp.ClientSession, artist: str, title: str
) -> dict:
    async with client.post(
        urljoin(REC_API_BASE_URL, "search/v2"),
        json={
            "query": f"{artist} {title}",
            "entities": {"releases": ["albums", "eps", "singles"]},
            "size": 24,
            "page": 1,
        },
    ) as response:
        return await response.json()


async def get_artist_releases(
    client: aiohttp.ClientSession, artist_slug: str
) -> Iterable[Release]:
    async with client.get(
        urljoin(REC_API_BASE_URL, f"artists/{artist_slug}/releases"),
        params={"limit": 20, "sortBy": "date-added-desc"},
    ) as response:
        data = await response.json()

        return (
            Release(
                title=release.get("title"),
                artist=_get_primary_artist(release),
                page_relative_url=release.get("uri"),
            )
            for release in data.get("data", [])
        )


def _normalize_artist_name(artist: str) -> str:
    artist = artist.lower().strip()
    artist = unartist(artist)
    artist = unaccent(artist)

    return artist


def _normalize_release_title(title: str) -> str:
    title = title.lower().strip()
    title = unaccent(title)

    return title
