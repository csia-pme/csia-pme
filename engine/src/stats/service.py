from services.models import Service
from tasks.models import TaskStatus
from logger import Logger
from storage import Storage
from fastapi import Depends
from sqlmodel import Session, func, select
from database import get_session
from tasks.models import Task


class StatsService:
    def __init__(self, logger: Logger = Depends(), storage: Storage = Depends(),
                 session: Session = Depends(get_session)):
        self.logger = logger
        self.storage = storage
        self.session = session

    def stats(self):
        running = 0
        finished = 0
        error = 0
        pending = 0
        unavailable = 0

        task_service = self.session.query(Task).all()

        services_tasks_count = dict()
        pipeline_tasks_count = dict()
        for task in task_service:
            if task.pipeline is not None:
                if task.pipeline.name not in pipeline_tasks_count:
                    pipeline_tasks_count[task.pipeline.name] = 1
                else:
                    pipeline_tasks_count[task.pipeline.name] += 1
            else:
                if task.service.name not in services_tasks_count:
                    services_tasks_count[task.service.name] = 1
                else:
                    services_tasks_count[task.service.name] += 1

        task_total = self.session.query(Task).count()

        task_status_count = self.session.query(Task.status, func.count(Task.status)).group_by(Task.status).all()
        self.logger.info(task_status_count)
        for task in task_status_count:
            if task[0] == TaskStatus.RUNNING:
                running = task[1]
            elif task[0] == TaskStatus.FINISHED:
                finished = task[1]
            elif task[0] == TaskStatus.ERROR:
                error = task[1]
            elif task[0] == TaskStatus.PENDING:
                pending = task[1]
            elif task[0] == TaskStatus.UNAVAILABLE:
                unavailable = task[1]

        stats = {"tasks": {"total": task_total,
                           "running": running,
                           "finished": finished,
                           "pending": pending,
                           "error": error,
                           "unavailable": unavailable},
                 "services": services_tasks_count,
                 "pipelines": pipeline_tasks_count}

        return stats
