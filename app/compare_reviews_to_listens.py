import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin

from sanic import DefaultSanic, Sanic

from app.api.lastfm import Album, get_weekly_albums
from app.api.rec import Release, get_recent_queue
from app.util.unaccent import unaccent
from settings import REC_BASE_URL


@dataclass(eq=True, frozen=True)
class ComparisonResult:
    title: str
    artist: str
    page_url: str

    @staticmethod
    def from_recent(recent: Release) -> "ComparisonResult":
        return ComparisonResult(
            title=recent.title,
            artist=recent.artist,
            page_url=urljoin(REC_BASE_URL, recent.page_relative_url),
        )

    @staticmethod
    def from_weekly(weekly: Album) -> "ComparisonResult":
        return ComparisonResult(
            title=weekly.title,
            artist=weekly.artist,
            page_url=weekly.page_url,
        )


async def compare_reviews_to_listens():
    _app: DefaultSanic = Sanic.get_app()

    recent_queue, weekly_albums = await asyncio.gather(
        get_recent_queue(_app.ctx.aio), get_weekly_albums(_app.ctx.aio)
    )

    only_in_recent: set[ComparisonResult] = set(
        ComparisonResult.from_recent(recent) for recent in recent_queue
    )
    only_in_weekly: set[ComparisonResult] = set(
        ComparisonResult.from_weekly(weekly) for weekly in weekly_albums
    )
    both: set[ComparisonResult] = set()

    for recent in recent_queue:
        n_left = unaccent(recent.title).lower()

        for weekly in weekly_albums:
            n_right = unaccent(weekly.title).lower()

            # TODO
            # - doesn't handle same name different artist
            # - doesn't handle different language titles
            # - doesn't handle titles with (special) (limited) (etc) in them
            if n_left == n_right:
                both.add(ComparisonResult.from_recent(recent))

                only_in_recent.remove(ComparisonResult.from_recent(recent))
                only_in_weekly.remove(ComparisonResult.from_weekly(weekly))
                break

    return only_in_recent, only_in_weekly, both
