from typing import Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    name: Optional[str] = None
    extension: Optional[str] = None
    size: Optional[int] = None
    thumb: Optional[str] = None
    downloadUrl: Optional[str] = None


class StatusResponse(BaseModel):
    ok: bool
    status: str
    file: Optional[FileInfo] = None
