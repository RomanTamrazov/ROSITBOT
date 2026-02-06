from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from pydantic import BaseModel, Field, ConfigDict
    _PYDANTIC_V2 = True
except Exception:  # pragma: no cover
    from pydantic import BaseModel, Field  # type: ignore
    _PYDANTIC_V2 = False


@dataclass
class Entity:
    type: str
    text: str
    start: int
    end: int


@dataclass
class LinkedLocation:
    text: str
    id: str
    score: float


class Command(BaseModel):
    cmd: str
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None

    if _PYDANTIC_V2:
        model_config = ConfigDict(populate_by_name=True)
    else:
        class Config:  # pydantic v1 fallback
            allow_population_by_field_name = True


class ParseRequest(BaseModel):
    text: str
    strict: Optional[bool] = None


class ParseResponse(BaseModel):
    status: str
    plan: Optional[list[Command]] = None
    message: Optional[str] = None
    needs_clarification: Optional[bool] = None
