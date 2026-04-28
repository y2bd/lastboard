import aiohttp
from sanic import DefaultSanic, Request, Sanic, redirect
from sanic.log import logger
from sanic_ext import render

from app.compare_reviews_to_listens import compare_reviews_to_listens
from app.release_detail import get_release_detail
from settings import USER_AGENT

app = Sanic("lastboard")

app.static("/resources", "./static", name="resources")


@app.before_server_start
async def attach_aio(app: DefaultSanic):
    client_session = aiohttp.ClientSession(loop=app.loop)
    client_session.headers["User-Agent"] = USER_AGENT
    client_session.headers["Content-Type"] = "application/json"

    app.ctx.aio = client_session


@app.after_server_stop
async def detach_aio(app: DefaultSanic):
    aio: aiohttp.ClientSession = app.ctx.aio
    await aio.close()


@app.get("/")
@app.ext.template("index.html.jinja", name="index")
async def index(request: Request):
    unrelated, pending, reviewed = await compare_reviews_to_listens()

    pending = sorted(pending, key=lambda p: p.listens, reverse=True)
    unrelated = sorted(unrelated, key=lambda p: f"{p.artist} - {p.title}")
    reviewed = sorted(reviewed, key=lambda p: f"{p.artist} - {p.title}")

    return await render(
        context={"unrelated": unrelated, "pending": pending, "reviewed": reviewed}
    )


@app.get("/release/<slug_hash:str>", name="release")
async def release(request: Request, slug_hash: str):
    logger.info(f"Release detail request for {slug_hash}")
    release_detail = await get_release_detail(slug_hash)
    logger.info(f"Redirecting to {release_detail.rec_url}")
    return redirect(release_detail.rec_url)
