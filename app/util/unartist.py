import re

from sanic.log import logger

_remove_ft = re.compile(r" (feat|ft)\. .+$", re.IGNORECASE)
_remove_amp = re.compile(r" & .+$", re.IGNORECASE)


def unartist(artist: str) -> str:
    relevant = "feat" in artist or "ft" in artist or "&" in artist

    if relevant:
        logger.debug("unartisting %s", artist)

    artist = re.sub(_remove_ft, "", artist)
    artist = re.sub(_remove_amp, "", artist)

    if relevant:
        logger.debug("unartisted to %s", artist)

    return artist
