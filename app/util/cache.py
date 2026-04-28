import json
from collections.abc import Coroutine
from pathlib import Path
from time import time
from typing import Any, TypeVar

from aiofile import async_open
from sanic.log import logger

from app.util.filename import sanitize_filename

T = TypeVar("T")


async def cache_or_run(
    cache_key: str,
    coroutine: Coroutine[Any, Any, T],
    cache_time_seconds: int = 60 * 60,  # 1 hour
) -> tuple[T, int]:
    current_time = int(time())

    base_path = Path.cwd()
    data_path = base_path / "data" / f"{sanitize_filename(cache_key)}.json"

    # grab cache
    # see if it exists and is fresh
    # if so, return it
    if data_path.exists():
        modified_time = int(data_path.stat().st_mtime)
        logger.debug(f"Cache file {cache_key} modified at {modified_time}")
        if current_time - modified_time <= cache_time_seconds:
            async with async_open(data_path, "r") as f:
                cached_json = json.loads(await f.read())
                cached_data: T | None = cached_json.get("data")

                if cached_data is not None:
                    coroutine.close()
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data, modified_time

    # otherwise, run the coroutine and cache the result
    result = await coroutine
    data_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_open(data_path, "w") as f:
        await f.write(json.dumps({"time": current_time, "data": result}))

    return result, current_time
