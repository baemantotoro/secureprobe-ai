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
