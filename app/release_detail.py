from dataclasses import dataclass
from urllib.parse import urljoin

from aiohttp.client import ClientSession
from sanic import Sanic
from sanic.exceptions import NotFound

from app.api.rec import search_release
from app.util.slug import load_slug
from settings import REC_BASE_URL


@dataclass
class ReleaseDetail:
    title: str
    artist: str

    rec_url: str
    lastfm_url: str

    tracks: list["Track"]


@dataclass
class Track:
    title: str
    duration_secs: int


async def get_release_detail(slug_hash: str) -> ReleaseDetail:
    _app = Sanic.get_app()
    client: ClientSession = _app.ctx.aio

    slug = await load_slug(slug_hash)
    if slug is None:
        raise NotFound(f"Release not found for slug {slug_hash}")

    rec_release = await search_release(client, slug)
    if rec_release is None:
        raise NotFound(f"Release not found for {slug.artist} - {slug.title}")

    return ReleaseDetail(
        title=rec_release.title,
        artist=rec_release.artist,
        rec_url=urljoin(REC_BASE_URL, rec_release.page_relative_url),
        lastfm_url="",
        tracks=[],
    )
