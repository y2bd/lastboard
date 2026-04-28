import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from aiofile import async_open

Slug = NamedTuple("Slug", [("title", str), ("artist", str)])


async def emit_slug(slug: Slug):
    slug_hash = hashlib.shake_256(str(slug).encode()).hexdigest(8)

    base_path = Path.cwd()
    slug_path = base_path / "data" / "slugs" / f"{slug_hash}.json"

    if not slug_path.exists():
        slug_path.parent.mkdir(parents=True, exist_ok=True)
        async with async_open(slug_path, "w") as f:
            await f.write(json.dumps(slug._asdict()))

    return slug_hash


async def load_slug(slug_hash: str) -> Slug | None:
    base_path = Path.cwd()
    slug_path = base_path / "data" / "slugs" / f"{slug_hash}.json"

    if not slug_path.exists():
        return None

    async with async_open(slug_path, "r") as f:
        slug_data = await f.read()
        slug_dict = json.loads(slug_data)
        return Slug(**slug_dict)
