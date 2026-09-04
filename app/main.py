from fastapi import FastAPI, Query, HTTPException

from .models import StatusResponse
from .validators import validate_diskwala_url
from .resolver import resolve_diskwala


app = FastAPI(
    title="DiskWala Resolver API",
    description="API for resolving publicly accessible DiskWala file information.",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "DiskWala Resolver API",
        "status": "online",
        "version": "1.0.0"
    }


@app.head("/")
async def root_head():
    return


@app.get("/health")
async def health():
    return {
        "ok": True,
        "status": "healthy"
    }


@app.get(
    "/web/api/status",
    response_model=StatusResponse
)
async def status(
    link: str = Query(
        ...,
        description="Public DiskWala URL"
    )
):
    # Validate URL
    if not validate_diskwala_url(link):
        raise HTTPException(
            status_code=400,
            detail="Invalid DiskWala URL"
        )

    try:
        # Resolve publicly accessible information
        file_info = await resolve_diskwala(link)

        # No publicly available download URL
        if not file_info.downloadUrl:
            return StatusResponse(
                ok=True,
                status="processing",
                file=file_info
            )

        # Successfully resolved
        return StatusResponse(
            ok=True,
            status="done",
            file=file_info
        )

    except Exception as exc:
        print(f"Resolver error: {exc}")

        return StatusResponse(
            ok=False,
            status="failed",
            file=None
        )
