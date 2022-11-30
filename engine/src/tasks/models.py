from typing import List
from sqlmodel import Field, JSON, Column, SQLModel, Relationship

from .enums import TaskStatus
from common.models import CoreModel
from pipelines.models import Pipeline
from services.models import Service
from uuid import UUID, uuid4


class TaskBase(CoreModel):
    """
    Base class for Task
    This model is used in subclasses
    """
    data_in: List[str] | None = Field(sa_column=Column(JSON), default=None, nullable=True)
    data_out: List[str] | None = Field(sa_column=Column(JSON), default=None, nullable=True)
    status: TaskStatus = Field(default=TaskStatus.PENDING, nullable=False)
    service_id: UUID = Field(nullable=False, foreign_key="service.id")
    pipeline_id: UUID | None = Field(default=None, nullable=True, foreign_key="pipeline.id")

    # Needed for Column(JSON) to work
    class Config:
        arbitrary_types_allowed = True


class Task(TaskBase, table=True):
    """
    Task model
    This model is the one that is stored in the database
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    service: Service = Relationship(back_populates="tasks")
    pipeline: Pipeline | None = Relationship(back_populates="tasks")


class TaskRead(TaskBase):
    """
    Task read model
    This model is used to return a task to the user
    """
    id: UUID


class TaskReadWithServiceAndPipeline(TaskRead):
    """
    Task read model with service
    This model is used to return a task to the user with the service
    """
    service: Service
    pipeline: Pipeline | None


class TaskCreate(TaskBase):
    """
    Task create model
    This model is used to create a task
    """
    pass


class TaskUpdate(SQLModel):
    """
    Task update model
    This model is used to update a task
    """
    service: str | None
    url: str | None
    data_out: List[str] | None
    status: TaskStatus | None
