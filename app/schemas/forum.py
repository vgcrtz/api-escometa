from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ForumAttachmentCreate(BaseModel):
    url: str
    storage_path: Optional[str] = None
    original_name: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class ForumCommunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None


class ForumCommunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None
    active: Optional[bool] = None


class ForumMessageCreate(BaseModel):
    content: Optional[str] = None
    message_type: str = "TEXT"
    reply_message_id: Optional[int] = None
    attachments: Optional[List[ForumAttachmentCreate]] = None


class ForumMessageUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class ForumPinUpdate(BaseModel):
    pinned: bool = True


class ForumUserResponse(BaseModel):
    id_usuario: int
    nombre: Optional[str] = None
    nombre_usuario: Optional[str] = None
    correo: Optional[str] = None
    foto_perfil_url: Optional[str] = None


class ForumCommunityResponse(BaseModel):
    id_community: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    active: bool


class ForumMessageResponse(BaseModel):
    id_message: int
    id_community: int
    id_sender: int
    content: Optional[str] = None
    message_type: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    edited: bool
    deleted: bool
    pinned: bool
    reply_message_id: Optional[int] = None
