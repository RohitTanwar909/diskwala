import json
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .models import FileInfo


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


MEDIA_EXTENSIONS = (
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".mp3",
    ".m4a",
    ".zip",
    ".rar",
    ".pdf",
)


def clean_url(value: str, base_url: str) -> str:
    value = value.strip().strip("\"'")

    if value.startswith("//"):
        return "https:" + value

    return urljoin(base_url, value)


def find_media_urls(text: str, base_url: str):
    pattern = r'https?://[^"\'<>\s]+'

    results = []

    for value in re.findall(pattern, text):
        value = value.rstrip("),]}")

        lower = value.lower()

        if any(ext in lower for ext in MEDIA_EXTENSIONS):
            results.append(value)

    return list(dict.fromkeys(results))


def recursive_find(data, keys):
    if isinstance(data, dict):
        for key, value in data.items():

            if key.lower() in keys and isinstance(value, str):
                if value.startswith(("http://", "https://", "/")):
                    return value

            found = recursive_find(value, keys)

            if found:
                return found

    elif isinstance(data, list):
        for item in data:
            found = recursive_find(item, keys)

            if found:
                return found

    return None


def recursive_find_number(data, keys):
    if isinstance(data, dict):
        for key, value in data.items():

            if key.lower() in keys:
                if isinstance(value, int):
                    return value

                if isinstance(value, str) and value.isdigit():
                    return int(value)

            found = recursive_find_number(value, keys)

            if found is not None:
                return found

    elif isinstance(data, list):
        for item in data:
            found = recursive_find_number(item, keys)

            if found is not None:
                return found

    return None


async def resolve_diskwala(url: str) -> FileInfo:

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    timeout = httpx.Timeout(
        connect=15,
        read=30,
        write=15,
        pool=15,
    )

    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as client:

        response = await client.get(url)
        response.raise_for_status()

        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    file_name = None
    extension = None
    file_size = None
    thumbnail = None
    download_url = None

    # ---------------------------------------------------------
    # 1. OpenGraph metadata
    # ---------------------------------------------------------

    og_title = soup.find("meta", property="og:title")

    if og_title:
        value = og_title.get("content")

        if value:
            file_name = value.strip()

    og_image = soup.find("meta", property="og:image")

    if og_image:
        thumbnail = clean_url(
            og_image.get("content", ""),
            url,
        )

    # ---------------------------------------------------------
    # 2. Video / audio HTML elements
    # ---------------------------------------------------------

    for tag in soup.find_all(["video", "audio", "source"]):

        src = tag.get("src")

        if not src:
            continue

        candidate = clean_url(src, url)

        if any(
            ext in candidate.lower()
            for ext in MEDIA_EXTENSIONS
        ):
            download_url = candidate
            break

    # ---------------------------------------------------------
    # 3. JSON-LD
    # ---------------------------------------------------------

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:
            data = json.loads(script.string or "")

            if isinstance(data, list):

                for item in data:

                    candidate = recursive_find(
                        item,
                        {
                            "contenturl",
                            "content_url",
                            "downloadurl",
                            "download_url",
                        },
                    )

                    if candidate:
                        download_url = clean_url(
                            candidate,
                            url,
                        )
                        break

            else:

                candidate = recursive_find(
                    data,
                    {
                        "contenturl",
                        "content_url",
                        "downloadurl",
                        "download_url",
                    },
                )

                if candidate:
                    download_url = clean_url(
                        candidate,
                        url,
                    )

        except Exception:
            continue

        if download_url:
            break

    # ---------------------------------------------------------
    # 4. Embedded JSON / JavaScript
    # ---------------------------------------------------------

    json_candidates = []

    for script in soup.find_all("script"):

        content = script.string

        if not content:
            continue

        json_candidates.append(content)

    for text in json_candidates:

        # Look for explicit download URL fields
        patterns = [
            r'"downloadUrl"\s*:\s*"([^"]+)"',
            r'"download_url"\s*:\s*"([^"]+)"',
            r'"directUrl"\s*:\s*"([^"]+)"',
            r'"direct_url"\s*:\s*"([^"]+)"',
            r'"contentUrl"\s*:\s*"([^"]+)"',
            r'"content_url"\s*:\s*"([^"]+)"',
        ]

        for pattern in patterns:

            match = re.search(pattern, text)

            if match:

                download_url = clean_url(
                    match.group(1),
                    url,
                )

                break

        if download_url:
            break

    # ---------------------------------------------------------
    # 5. Look for direct media URLs
    # ---------------------------------------------------------

    if not download_url:

        media_urls = find_media_urls(
            html,
            url,
        )

        if media_urls:
            download_url = media_urls[0]

    # ---------------------------------------------------------
    # 6. Extract extension
    # ---------------------------------------------------------

    if download_url:

        match = re.search(
            r"\.([a-zA-Z0-9]{2,5})(?:\?|#|$)",
            download_url,
        )

        if match:
            extension = match.group(1).lower()

    # ---------------------------------------------------------
    # 7. Try filename
    # ---------------------------------------------------------

    if download_url and not file_name:

        filename_match = re.search(
            r"/([^/?#]+?)(?:\?|#|$)",
            download_url,
        )

        if filename_match:
            file_name = filename_match.group(1)

    return FileInfo(
        name=file_name,
        extension=extension,
        size=file_size,
        thumb=thumbnail,
        downloadUrl=download_url,
    )
