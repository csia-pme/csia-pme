from sqlmodel import Field, SQLModel, Column, DateTime, func
from datetime import datetime
from typing import List


class CoreModel(SQLModel):
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )


class FieldDescription(SQLModel):
    name: str = Field(str, nullable=False)
    type: str = Field(str, nullable=False)


class APIDescription(SQLModel):
    route: str
    summary: str | None
    description: str | None
    body: str | dict | List[str]
    bodyType: str | List[str] | None
    resultType: str | None
