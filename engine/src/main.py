from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pipelines.controller import router as pipelines_router
from services.controller import router as services_router
from stats.controller import router as stats_router
from tasks.controller import router as tasks_router

api_description = """
CSIA-PME API - The **best** API in the world.
"""

# Define the FastAPI application with information
app = FastAPI(
    title="CSIA-PME API",
    description=api_description,
    version="0.0.1",
    contact={
        "name": "CSIA-PME",
        "url": "https://swiss-ai-center.ch/",
        "email": "info@swiss-ai-center.ch",
    },
    swagger_ui_parameters={
        "tagsSorter": "alpha",
        "operationsSorter": "method",
    },
    # TODO: Add license information
    # license_info={
    #     "name": "",
    #     "url": "",
    # },
)

# Include routers from other files
app.include_router(pipelines_router, tags=['Pipelines'])
app.include_router(services_router, tags=['Services'])
app.include_router(stats_router, tags=['Stats'])
app.include_router(tasks_router, tags=['Tasks'])


# Redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs", status_code=301)
