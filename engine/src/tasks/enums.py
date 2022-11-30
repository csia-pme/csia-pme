from enum import Enum


class TaskStatus(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"
    PENDING = "pending"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
