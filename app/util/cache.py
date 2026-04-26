import json
from pathlib import Path
from time import time
from typing import Any, Coroutine, TypeVar

from aiofile import async_open
from sanic.log import logger

T = TypeVar("T")


async def cache_or_run(
    cache_key: str,
    coroutine: Coroutine[T, Any, Any],
    cache_time_seconds: int = 60 * 60,  # 1 hour
) -> T:
    current_time = int(time())

    base_path = Path.cwd()
    data_path = base_path / "data" / f"{cache_key}.json"

    # grab cache
    # see if it exists and is fresh
    # if so, return it
    if data_path.exists():
        async with async_open(data_path, "r") as f:
            cached_json = json.loads(await f.read())
            cached_time: int | None = cached_json.get("time")
            cached_data: T | None = cached_json.get("data")

            if (
                cached_time is not None
                and current_time - cached_time <= cache_time_seconds
                and cached_data is not None
            ):
                coroutine.close()
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data

    # otherwise, run the coroutine and cache the result
    result = await coroutine
    data_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_open(data_path, "w") as f:
        await f.write(json.dumps({"time": current_time, "data": result}))

    return result
