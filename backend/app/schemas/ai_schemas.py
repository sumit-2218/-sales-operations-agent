"""Schemas for validating what the local model returns."""
from pydantic import BaseModel, Field, field_validator


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    return v


class LeadExplanation(BaseModel):
    summary: str = Field(min_length=10, max_length=2000)
    positive_factors: list[str] = Field(default_factory=list, max_length=12)
    negative_factors: list[str] = Field(default_factory=list, max_length=12)
    missing_information: list[str] = Field(default_factory=list, max_length=12)
    recommended_next_steps: list[str] = Field(default_factory=list, max_length=12)
    data_limitations: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("positive_factors", "negative_factors", "missing_information",
                     "recommended_next_steps", "data_limitations", mode="before")
    @classmethod
    def _lists(cls, v):
        return _as_list(v)

    def all_text(self) -> str:
        parts = [self.summary, *self.positive_factors, *self.negative_factors, *self.missing_information,
                 *self.recommended_next_steps, *self.data_limitations]
        return "\n".join(parts)


class OutreachOutput(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    body: str = Field(min_length=20, max_length=5000)
    channel: str | None = None
    personalization_note: str = Field(default="", max_length=1000)

    @field_validator("personalization_note", mode="before")
    @classmethod
    def _note(cls, v):
        return "" if v is None else v

    def all_text(self) -> str:
        return "\n".join([self.subject or "", self.body, self.personalization_note])
