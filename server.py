import aiohttp
from sanic import DefaultSanic, Request, Sanic
from sanic_ext import render

from app.compare_reviews_to_listens import compare_reviews_to_listens

app = Sanic("lastboard")


@app.before_server_start
async def attach_aio(app: DefaultSanic):
    app.ctx.aio = aiohttp.ClientSession(loop=app.loop)


@app.after_server_stop
async def detach_aio(app: DefaultSanic):
    aio: aiohttp.ClientSession = app.ctx.aio
    await aio.close()


@app.get("/")
@app.ext.template("index.html.jinja")
async def hello_world(request: Request):
    unrelated, pending, reviewed = await compare_reviews_to_listens()
    return await render(
        context={"unrelated": unrelated, "pending": pending, "reviewed": reviewed}
    )
