import logging
from typing import Iterator, List

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


def new_join_url_segs(*url_segs: Iterator[str], delimeter=PuncEnum.SLASH.value) -> str:
    """
    Remove extra delimeter or add missing delimeter to join url segments
    """
    if not url_segs:
        raise ValueError("The parameter 'url_segs' is not provided")
    url_segs = [url_seg.strip(delimeter) for url_seg in url_segs if url_seg]
    url = delimeter.join(url_segs)
    if not url:
        raise ValueError("The 'url' is empty")
    return url
