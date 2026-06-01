from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, BigInteger, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ForumCommunity(Base):
    __tablename__ = "forum_communities"

    id_community = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, nullable=False, default=True)

    messages = relationship(
        "ForumMessage",
        back_populates="community",
        cascade="all, delete-orphan",
    )


class ForumMessage(Base):
    __tablename__ = "forum_messages"

    id_message = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_community = Column(
        Integer,
        ForeignKey("forum_communities.id_community", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_sender = Column(
        Integer,
        ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=True)
    message_type = Column(Enum("TEXT", "IMAGE", "FILE", "SYSTEM"), nullable=False, default="TEXT")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    edited_at = Column(DateTime, nullable=True)
    edited = Column(Boolean, nullable=False, default=False)
    deleted = Column(Boolean, nullable=False, default=False)
    pinned = Column(Boolean, nullable=False, default=False)
    reply_message_id = Column(
        Integer,
        ForeignKey("forum_messages.id_message", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )

    community = relationship("ForumCommunity", back_populates="messages")
    attachments = relationship(
        "ForumAttachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    reply_message = relationship("ForumMessage", remote_side=[id_message])


class ForumAttachment(Base):
    __tablename__ = "forum_attachments"

    id_attachment = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_message = Column(
        Integer,
        ForeignKey("forum_messages.id_message", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url = Column(Text, nullable=False)
    storage_path = Column(String(255), nullable=True)
    original_name = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    message = relationship("ForumMessage", back_populates="attachments")
