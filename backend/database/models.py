from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    rtsp_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

    settings = relationship("StreamSettings", back_populates="stream", uselist=False)
    boxes = relationship("SelectionBox", back_populates="stream")


class StreamSettings(Base):
    __tablename__ = "stream_settings"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), unique=True)

    threshold = Column(Integer, default=127)
    rotate = Column(Integer, default=0)
    auto_rotate = Column(Boolean, default=False)

    crop_x = Column(Integer, default=0)
    crop_y = Column(Integer, default=0)
    crop_w = Column(Integer, default=100)
    crop_h = Column(Integer, default=100)

    stream = relationship("Stream", back_populates="settings")


class SelectionBox(Base):
    __tablename__ = "selection_boxes"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("streams.id"))

    x = Column(Integer)
    y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    label = Column(String, nullable=True)

    stream = relationship("Stream", back_populates="boxes")
