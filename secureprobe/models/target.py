"""Minimal endpoint metadata for passive HTML collection."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
