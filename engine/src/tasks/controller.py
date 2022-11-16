from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from .service import TasksService
from .schemas.task import TaskSchema
from common.query_parameters.skip_and_limit import SkipAndLimit

router = APIRouter()


@router.get("/tasks/{task_id}", summary="Get results of a task", responses={404: {"description": "Task Not Found"}},
            response_model=TaskSchema)
async def get_task_result(task_id: str, tasks_service: TasksService = Depends()):
    task = tasks_service.find_one(task_id)

    if task == None:
        raise HTTPException(status_code=404)

    dto = TaskSchema.toTaskSchema(task)

    return dto


@router.get("/tasks", summary="Find many tasks", description="Find many tasks.", response_model=list[TaskSchema])
async def get_many_tasks(skip_and_limit: SkipAndLimit = Depends(), tasks_service: TasksService = Depends()):
    tasks = tasks_service.find_many(skip_and_limit.skip, skip_and_limit.limit)

    dtos = []

    for task in tasks:
        taskDto = TaskSchema.toTaskSchema(task)
        dtos.append(taskDto)

    return dtos


@router.post("/tasks", summary="Create a task", description="Create a task.", response_model=TaskSchema)
async def create(tasks_service: TasksService = Depends()):
    task = tasks_service.create()

    dto = TaskSchema.toTaskSchema(task)

    return dto
