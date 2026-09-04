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

        if parsed.hostname not in ALLOWED_HOSTS:
            return False

        if not parsed.path.startswith("/app/"):
            return False

        return True

    except Exception:
        return False
