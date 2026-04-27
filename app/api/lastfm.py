from dataclasses import dataclass
from urllib.parse import urljoin

import aiohttp
from sanic.log import logger

from app.util.cache import cache_or_run
from app.util.unartist import unartist
from settings import DEFAULT_LAST_FM_USER, LAST_FM_API_KEY


@dataclass
class Album:
    title: str
    artist: str
    play_count: int
    page_url: str

    def key(self) -> tuple[str, str]:
        return (self.title, self.artist)

    def __eq__(self, value: object, /) -> bool:
        return (
            isinstance(value, Album)
            and self.title == value.title
            and self.artist == value.artist
        )

    def __str__(self) -> str:
        return f"{self.artist} - {self.title} ({self.play_count} play(s))"


async def get_weekly_albums(
    client: aiohttp.ClientSession, user: str = DEFAULT_LAST_FM_USER
) -> list:
    (response_dict, _) = await cache_or_run(
        "weekly_albums", _get_weekly_albums_request(client, user)
    )

    data: list = response_dict.get("weeklyalbumchart", {}).get("album", [])

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


async def get_recent_albums(
    client: aiohttp.ClientSession, user: str = DEFAULT_LAST_FM_USER
) -> list:
    async def _two_page() -> list:
        page_1 = await _get_tracks_request(client, user, 1)
        page_2 = await _get_tracks_request(client, user, 2)
        return page_1.get("recenttracks", {}).get("track", []) + page_2.get(
            "recenttracks", {}
        ).get("track", [])

    (two_pages, _) = await cache_or_run("recent_tracks", _two_page())

    logger.debug(f"Fetched {len(two_pages)} recent tracks for user {user}")

    recent_albums: dict[tuple[str, str], Album] = {}
    for track in two_pages:
        track_album_name: str = track.get("album", {}).get("#text", "")
        track_artist: str = unartist(track.get("artist", {}).get("#text", ""))
        track_album_url_maybe: str = urljoin(
            "https://www.last.fm/music/", f"{track_artist}/{track_album_name}"
        )

        if not track_album_name or not track_artist:
            continue

        existing = recent_albums.get((track_album_name, track_artist))
        if existing:
            existing.play_count += 1
        else:
            recent_albums[(track_album_name, track_artist)] = Album(
                title=track_album_name,
                artist=track_artist,
                play_count=1,
                page_url=track_album_url_maybe,
            )

    return sorted(
        list(recent_albums.values()), key=lambda a: a.play_count, reverse=True
    )


async def _get_tracks_request(
    client: aiohttp.ClientSession, user: str, page: int = 1
) -> dict:
    async with client.get(
        "https://ws.audioscrobbler.com/2.0/",
        params={
            "method": "user.getrecenttracks",
            "user": user,
            "page": page,
            "limit": 200,
            "api_key": LAST_FM_API_KEY,
            "format": "json",
        },
    ) as response:
        logger.debug(f"Fetched tracks page {page} for user {user}")
        return await response.json()
