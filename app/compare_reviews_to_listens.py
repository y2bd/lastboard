import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin

from sanic import DefaultSanic, Sanic

from app.api.lastfm import Album, get_recent_albums
from app.api.rec import Release, get_recent_queue
from app.util.unaccent import unaccent
from settings import REC_BASE_URL


@dataclass(eq=True, frozen=True)
class ComparisonResult:
    title: str
    artist: str
    page_url: str
    listens: int | None

    @staticmethod
    def from_recent(recent: Release) -> "ComparisonResult":
        return ComparisonResult(
            title=recent.title,
            artist=recent.artist,
            page_url=urljoin(REC_BASE_URL, recent.page_relative_url),
            listens=None,
        )

    @staticmethod
    def from_weekly(weekly: Album) -> "ComparisonResult":
        return ComparisonResult(
            title=weekly.title,
            artist=weekly.artist,
            page_url=weekly.page_url,
            listens=weekly.play_count,
        )


async def compare_reviews_to_listens():
    _app: DefaultSanic = Sanic.get_app()

    rec_queue, lastfm_queue = await asyncio.gather(
        get_recent_queue(_app.ctx.aio), get_recent_albums(_app.ctx.aio)
    )

    only_in_rec: set[ComparisonResult] = set(
        ComparisonResult.from_recent(recent) for recent in rec_queue
    )
    only_in_lastfm: set[ComparisonResult] = set(
        ComparisonResult.from_weekly(weekly) for weekly in lastfm_queue
    )
    both: set[ComparisonResult] = set()

    for recent in rec_queue:
        n_left = unaccent(recent.title).lower()

        for weekly in lastfm_queue:
            n_right = unaccent(weekly.title).lower()

            # TODO
            # - doesn't handle same name different artist
            # - doesn't handle different language titles
            # - doesn't handle titles with (special) (limited) (etc) in them
            if n_left == n_right:
                both.add(ComparisonResult.from_recent(recent))

                only_in_rec.remove(ComparisonResult.from_recent(recent))
                only_in_lastfm.remove(ComparisonResult.from_weekly(weekly))
                break

    return only_in_rec, only_in_lastfm, both
