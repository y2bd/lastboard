from dataclasses import dataclass

import aiohttp
from sanic.log import logger

from app.util.cache import cache_or_run
from settings import DEFAULT_LAST_FM_USER, LAST_FM_API_KEY


@dataclass
class Album:
    title: str
    artist: str
    play_count: int
    page_url: str

    def __str__(self) -> str:
        return f"{self.artist} - {self.title} ({self.play_count} play(s))"


async def get_weekly_albums(
    client: aiohttp.ClientSession, user: str = DEFAULT_LAST_FM_USER
) -> list:
    response_dict: dict = await cache_or_run(
        "weekly_albums", _get_weekly_albums_request(client, user)
    )

    data: dict = response_dict.get("weeklyalbumchart", {}).get("album", [])

    logger.debug(f"Fetched {len(data)} weekly albums for user {user}")

    return [
        Album(
            title=album.get("name", ""),
            artist=album.get("artist", {}).get("#text", ""),
            play_count=int(album.get("playcount", 0)),
            page_url=album.get("url", ""),
        )
        for album in data
    ]


async def _get_weekly_albums_request(client: aiohttp.ClientSession, user: str) -> dict:
    async with client.get(
        f"https://ws.audioscrobbler.com/2.0/?method=user.getweeklyalbumchart&user={user}&api_key={LAST_FM_API_KEY}&format=json"
    ) as response:
        logger.debug(f"Fetched weekly albums for user {user}")
        return await response.json()
