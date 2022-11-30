from fastapi import Depends
from storage import Storage
from sqlmodel import Session, select, desc
from database import get_session
from logger import Logger
from uuid import UUID
from .models import Task, TaskUpdate
from common.exception import NotFoundException


class TasksService:
    def __init__(self, logger: Logger = Depends(), storage: Storage = Depends(),
                 session: Session = Depends(get_session)):
        self.logger = logger
        self.storage = storage
        self.session = session

    def find_many(self, skip: int = 0, limit: int = 100):
        self.logger.debug("Find many tasks")
        return self.session.exec(select(Task).order_by(desc(Task.created_at)).offset(skip).limit(limit)).all()

    def create(self, task: Task):
        self.logger.debug("Creating task")

        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        self.logger.debug(f"Created task with id {task.id}")

        return task

    def find_one(self, task_id: UUID):
        self.logger.debug("Find task")

        return self.session.get(Task, task_id)

    def update(self, task_id: UUID, task: TaskUpdate):
        self.logger.debug("Update task")
        current_task = self.session.get(Task, task_id)
        if not current_task:
            raise NotFoundException("Task Not Found")
        task_data = task.dict(exclude_unset=True)
        self.logger.debug(f"Updating task {task_id} with data: {task_data}")
        for key, value in task_data.items():
            setattr(current_task, key, value)
        self.session.add(current_task)
        self.session.commit()
        self.session.refresh(current_task)
        self.logger.debug(f"Updated task with id {current_task.id}")
        return current_task

    def delete(self, task_id: UUID):
        self.logger.debug("Delete task")
        current_task = self.session.get(Task, task_id)
        if not current_task:
            raise NotFoundException("Task Not Found")
        self.session.delete(current_task)
        self.session.commit()
        self.logger.debug(f"Deleted task with id {current_task.id}")
