from fastapi import Depends
from storage import Storage
from sqlmodel import Session, select, desc
from database import get_session
from logger import Logger
from uuid import UUID
from .models import Service, ServiceUpdate
from common.exception import NotFoundException


class ServicesService:
    def __init__(self, logger: Logger = Depends(), storage: Storage = Depends(),
                 session: Session = Depends(get_session)):
        self.logger = logger
        self.storage = storage
        self.session = session

    def find_many(self, skip: int = 0, limit: int = 100):
        self.logger.debug("Find many services")
        return self.session.exec(select(Service).order_by(desc(Service.created_at)).offset(skip).limit(limit)).all()

    def create(self, service: Service):
        self.logger.debug("Creating service")

        self.session.add(service)
        self.session.commit()
        self.session.refresh(service)
        self.logger.debug(f"Created service with id {service.id}")

        return service

    def find_one(self, service_id: UUID):
        self.logger.debug("Find service")

        return self.session.get(Service, service_id)

    def update(self, service_id: UUID, service: ServiceUpdate):
        self.logger.debug("Update service")
        current_service = self.session.get(Service, service_id)
        if not current_service:
            raise NotFoundException("Service Not Found")
        service_data = service.dict(exclude_unset=True)
        self.logger.debug(f"Updating service {service_id} with data: {service_data}")
        for key, value in service_data.items():
            setattr(current_service, key, value)
        self.session.add(current_service)
        self.session.commit()
        self.session.refresh(current_service)
        self.logger.debug(f"Updated service with id {current_service.id}")
        return current_service

    def delete(self, service_id: UUID):
        self.logger.debug("Delete service")
        current_service = self.session.get(Service, service_id)
        if not current_service:
            raise NotFoundException("Service Not Found")
        self.session.delete(current_service)
        self.session.commit()
        self.logger.debug(f"Deleted service with id {current_service.id}")
