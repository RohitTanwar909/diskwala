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
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.get(
    "/web/api/status",
    response_model=StatusResponse
)
async def status(
    link: str = Query(..., description="DiskWala public URL")
):

    if not validate_diskwala_url(link):
        raise HTTPException(
            status_code=400,
            detail="Invalid DiskWala URL"
        )

    try:

        file_info = await resolve_diskwala(link)

        if not file_info.downloadUrl:
            return StatusResponse(
                ok=True,
                status="processing",
                file=file_info,
            )

        return StatusResponse(
            ok=True,
            status="done",
            file=file_info,
        )

    except Exception as exc:

        return StatusResponse(
            ok=False,
            status="failed",
            file=None,
        )
