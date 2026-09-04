from urllib.parse import urlparse


ALLOWED_HOSTS = {
    "diskwala.com",
    "www.diskwala.com",
}


def validate_diskwala_url(url: str) -> bool:
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()

        return hostname in ALLOWED_HOSTS

    except Exception:
        return False
