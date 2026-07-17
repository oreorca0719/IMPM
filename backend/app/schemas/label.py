"""라벨 DTO."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LabelCreate(BaseModel):
    name: str
    color: str = "#6B7280"


class LabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    color: str


class LabelAttach(BaseModel):
    label_id: int
