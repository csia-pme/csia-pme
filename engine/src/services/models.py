from typing import List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from common.models import CoreModel
from pipelines.models import PipelineServiceLink


class ServiceBase(CoreModel):
    """
    Base class for Service
    This model is used in subclasses
    """
    name: str = Field(nullable=False)
    url: str = Field(nullable=False)
    summary: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    # TODO: Should the `List[str]` be `List[FieldDescription]` where `FieldDesciption` consists of properties `name`, `type`?
    data_in_fields: List[str] | None = Field(sa_column=Column(JSON), default=None, nullable=True)
    # TODO: Should the `List[str]` be `List[FieldDescription]` where `FieldDesciption` consists of properties `name`, `type`?
    data_out_fields: List[str] | None = Field(sa_column=Column(JSON), default=None, nullable=True)

    # Needed for Column(JSON) to work
    class Config:
        arbitrary_types_allowed = True


class Service(ServiceBase, table=True):
    """
    Service model
    This model is the one that is stored in the database
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tasks: List["Task"] = Relationship(back_populates="service")
    pipelines: List["Pipeline"] = Relationship(back_populates="services", link_model=PipelineServiceLink)


class ServiceRead(ServiceBase):
    """
    Service read model
    This model is used to return a service to the user
    """
    id: UUID


class ServiceReadWithTasks(ServiceRead):
    """
    Service read model with tasks
    This model is used to return a service to the user with the tasks
    """
    from tasks.models import TaskRead
    tasks: List[TaskRead]


class ServiceCreate(ServiceBase):
    """
    Service create model
    This model is used to create a service
    """
    pass


class ServiceUpdate(SQLModel):
    """
    Service update model
    This model is used to update a service
    """
    name: str | None
    url: str | None
    summary: str | None
    description: str | None
    data_in_fields: List[str] | None
    data_out_fields: List[str] | None
