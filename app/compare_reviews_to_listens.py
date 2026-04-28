import asyncio
from dataclasses import dataclass

from sanic import DefaultSanic, Sanic

from app.api.lastfm import Album, get_recent_albums
from app.api.rec import Release, get_recent_queue
from app.util.filename import sanitize_filename
from app.util.slug import Slug, emit_slug
from app.util.unartist import unartist


@dataclass(eq=True, frozen=True)
class ComparisonResult:
    title: str
    artist: str
    slug_page: str
    listens: int | None

    def is_equivalent_to(self, other: "ComparisonResult") -> bool:
        return sanitize_filename(
            f"{unartist(self.artist)} - {self.title}"
        ) == sanitize_filename(f"{unartist(other.artist)} - {other.title}")

    @staticmethod
    async def from_rec_release(release: Release) -> "ComparisonResult":
        _app = Sanic.get_app()

        slug_hash = await emit_slug(Slug(title=release.title, artist=release.artist))
        slug_page = _app.url_for("release", slug_hash=slug_hash)

        return ComparisonResult(
            title=release.title,
            artist=release.artist,
            slug_page=slug_page,
            listens=None,
        )

    @staticmethod
    async def from_lastfm_album(album: Album) -> "ComparisonResult":
        _app = Sanic.get_app()

        slug_hash = await emit_slug(Slug(title=album.title, artist=album.artist))
        slug_page = _app.url_for("release", slug_hash=slug_hash)

        return ComparisonResult(
            title=album.title,
            artist=album.artist,
            slug_page=slug_page,
            listens=album.play_count,
        )


async def compare_reviews_to_listens():
    _app: DefaultSanic = Sanic.get_app()

    rec_queue, lastfm_queue = await asyncio.gather(
        get_recent_queue(_app.ctx.aio), get_recent_albums(_app.ctx.aio)
    )

    rec_comp = await asyncio.gather(
        *[ComparisonResult.from_rec_release(recent) for recent in rec_queue]
    )

    lastfm_comp = await asyncio.gather(
        *[ComparisonResult.from_lastfm_album(weekly) for weekly in lastfm_queue]
    )

    only_in_rec: set[ComparisonResult] = set(rec_comp)
    only_in_lastfm: set[ComparisonResult] = set(lastfm_comp)
    both: set[ComparisonResult] = set()

    for recent in rec_comp:
        for weekly in lastfm_comp:
            # TODO
            # - doesn't handle different language titles
            # - doesn't handle titles with (special) (limited) (etc) in them
            if recent.is_equivalent_to(weekly):
                both.add(recent)

                only_in_rec.remove(recent)
                only_in_lastfm.remove(weekly)
                break

    return only_in_rec, only_in_lastfm, both
