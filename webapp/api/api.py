from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pydantic

app = FastAPI()

app.mount("/static", StaticFiles(directory="api/static"), name="static")

templates = Jinja2Templates(directory="api/templates")

@app.get("/", response_class=HTMLResponse)
def get_index(
    request: Request,
):

    return templates.TemplateResponse(
        "index.template.html",
        {
            "request": request,
        },
    )
