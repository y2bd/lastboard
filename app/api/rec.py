from dataclasses import dataclass
from urllib.parse import urljoin

import aiohttp
from sanic.log import logger

from app.util.cache import cache_or_run
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
) -> list[Release]:
    response_dict = await cache_or_run(
        "releases", _get_recent_queue_request(client, user, limit)
    )

    data: list = response_dict.get("data", [])

    logger.debug(f"Fetched {len(data)} releases for user {user}")

    return [
        Release(
            title=release.get("title"),
            artist=_get_primary_artist(release),
            page_relative_url=release.get("uri"),
        )
        for release in data
    ]


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
