from typing import List
from sqlmodel import Field, SQLModel, Relationship

from common.models import CoreModel
from uuid import UUID, uuid4

class PipelineServiceLink(SQLModel, table=True):
    """
    PipelineServiceLink model
    This model is used to link a pipeline to a service
    """
    pipeline_id: UUID = Field(foreign_key="pipeline.id", primary_key=True)
    service_id: UUID = Field(foreign_key="service.id", primary_key=True)


class PipelineBase(CoreModel):
    """
    Base class for Pipeline
    This model is used in subclasses
    """
    name: str = Field(nullable=False)
    summary: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)


class Pipeline(PipelineBase, table=True):
    """
    Pipeline model
    This model is the one that is stored in the database
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    services: List["Service"] = Relationship(back_populates="pipelines", link_model=PipelineServiceLink)
    tasks: List["Task"] = Relationship(back_populates="pipeline")


class PipelineRead(PipelineBase):
    """
    Pipeline read model
    This model is used to return a pipeline to the user
    """
    id: UUID


class PipelineReadWithServiceAndTask(PipelineRead):
    """
    Pipeline read model with service
    This model is used to return a pipeline to the user with the service
    """
    from services.models import ServiceRead
    from tasks.models import TaskRead
    services: List[ServiceRead]
    tasks: List[TaskRead]


class PipelineCreate(PipelineBase):
    """
    Pipeline create model
    This model is used to create a pipeline
    """
    from services.models import ServiceRead
    services: List[UUID]
    pass


class PipelineUpdate(SQLModel):
    """
    Pipeline update model
    This model is used to update a pipeline
    """
    name: str | None
    url: str | None
    summary: str | None
    description: str | None
