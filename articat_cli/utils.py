import logging
from typing import List

from .enums import PuncEnum

logger = logging.getLogger(__file__)


def join_url_segs(urls: List[str], delimeter=PuncEnum.SLASH.value) -> str:
    """
    Remove extra delimeter or add missing delimeter to join url segments
    """
    assert urls, "The parameter 'urls' is empty"
    urls = [url.strip(delimeter) for url in urls if url]
    url = delimeter.join(urls)
    assert url, "The joined 'url' is empty"
    return url
