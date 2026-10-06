"""Minimal endpoint metadata for passive HTML collection."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EndpointParameter(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    location: Literal["query", "form"]


class Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: str = Field(min_length=1)
    method: Literal["GET", "POST"]
    source: Literal["current", "link", "form"]
    parameters: list[EndpointParameter] = Field(default_factory=list)


class FormField(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)

    @field_validator("type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.lower()


class Form(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(min_length=1)
    method: Literal["GET", "POST"]
    fields: list[FormField] = Field(default_factory=list)


class HeaderObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    present: bool = Field(strict=True)
    value: str | None = None
    note: str | None = None


class HeaderInspectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: str = Field(min_length=1)
    scheme: Literal["http", "https"]
    observations: list[HeaderObservation] = Field(default_factory=list)


class CookieInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    secure: bool = Field(strict=True)
    http_only: bool = Field(strict=True)
    same_site: Literal["Strict", "Lax", "None"] | None = None
    domain: str | None = None
    path: str | None = None
    max_age: int | None = None
    expires: str | None = None


class WebTargetContext(BaseModel):
    """Passive observations and hints, without raw bodies or cookie values."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    context_id: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    endpoints: list[Endpoint] = Field(default_factory=list)
    forms: list[Form] = Field(default_factory=list)
    headers: dict[str, str | None] = Field(default_factory=dict)
    cookies: list[CookieInfo] = Field(default_factory=list)
    authentication_detected: bool = Field(default=False, strict=True)
    session_detected: bool = Field(default=False, strict=True)
    content_types: list[str] = Field(default_factory=list)
