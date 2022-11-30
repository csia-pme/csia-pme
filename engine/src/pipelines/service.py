from fastapi import Depends
from storage import Storage
from sqlmodel import Session, select, desc
from database import get_session
from logger import Logger
from uuid import UUID
from .models import Pipeline, PipelineUpdate, PipelineServiceLink
from common.exception import NotFoundException


class PipelinesService:
    def __init__(self, logger: Logger = Depends(), storage: Storage = Depends(),
                 session: Session = Depends(get_session)):
        self.logger = logger
        self.storage = storage
        self.session = session

    def find_many(self, skip: int = 0, limit: int = 100):
        self.logger.debug("Find many pipelines")
        return self.session.exec(select(Pipeline).order_by(desc(Pipeline.created_at)).offset(skip).limit(limit)).all()

    def create(self, pipeline: Pipeline):
        self.logger.debug("Creating pipeline")

        self.session.add(pipeline)
        self.session.commit()
        self.session.refresh(pipeline)
        self.logger.debug(f"Created pipeline with id {pipeline.id}")

        return pipeline

    def find_one(self, pipeline_id: UUID):
        self.logger.debug("Find pipeline")

        return self.session.get(Pipeline, pipeline_id)

    def update(self, pipeline_id: UUID, pipeline: PipelineUpdate):
        self.logger.debug("Update pipeline")
        current_pipeline = self.session.get(Pipeline, pipeline_id)
        if not current_pipeline:
            raise NotFoundException("Pipeline Not Found")
        pipeline_data = pipeline.dict(exclude_unset=True)
        self.logger.debug(f"Updating pipeline {pipeline_id} with data: {pipeline_data}")
        for key, value in pipeline_data.items():
            setattr(current_pipeline, key, value)
        self.session.add(current_pipeline)
        self.session.commit()
        self.session.refresh(current_pipeline)
        self.logger.debug(f"Updated pipeline with id {current_pipeline.id}")
        return current_pipeline

    def delete(self, pipeline_id: UUID):
        self.logger.debug("Delete pipeline")
        current_pipeline = self.session.get(Pipeline, pipeline_id)
        if not current_pipeline:
            raise NotFoundException("Pipeline Not Found")
        self.session.delete(current_pipeline)
        self.session.commit()
        self.logger.debug(f"Deleted pipeline with id {current_pipeline.id}")
