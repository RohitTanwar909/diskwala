import re
import httpx
from bs4 import BeautifulSoup

from .models import FileInfo


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


async def resolve_diskwala(url: str):

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    timeout = httpx.Timeout(20.0)

    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as client:

        response = await client.get(url)

        response.raise_for_status()

        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Collect useful public metadata.
    title = None
    thumb = None
    download_url = None

    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title.get("content")

    og_image = soup.find("meta", property="og:image")
    if og_image:
        thumb = og_image.get("content")

    # Look for publicly exposed download URLs.
    urls = re.findall(
        r'https?://[^"\'>\s]+',
        html
    )

    for candidate in urls:
        lower = candidate.lower()

        if (
            ".mp4" in lower
            or ".mkv" in lower
            or ".webm" in lower
            or ".zip" in lower
            or ".pdf" in lower
            or "download" in lower
        ):
            download_url = candidate
            break

    extension = None

    if title and "." in title:
        extension = title.rsplit(".", 1)[-1].lower()

    return FileInfo(
        name=title,
        extension=extension,
        size=None,
        thumb=thumb,
        downloadUrl=download_url,
    )
