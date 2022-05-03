import os
import yaml
import pydantic
import io
import json
import datetime

from inspect import Parameter, Signature
from typing import Union
from fastapi import FastAPI, HTTPException, UploadFile, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from .Engine import Engine, Registry, Cron
from . import interface

def addRoute(route, body, summary=None, description=None):
	
	# This should be wrapped in a functor, howevera bug in starlette prevents the handler to be correctly called if __call__ is declared async. This should be fixed in version 0.21.0 (https://github.com/encode/starlette/pull/1444).
	async def handler(*args, **kwargs):
		jobData = {}
		binaries = []
		
		if type(body) is dict:
			jobData.update(kwargs["data"].dict())
		elif type(body) is str:
			binaries.append(body)
		elif type(body) is list:
			binaries = body
		
		if len(binaries) > 0:
			request = kwargs["req"]
			form = await request.form()
			for name in binaries:
				obj = form[name]
				if obj.content_type == "application/json":
					payload = await obj.read()
					jobData.update(json.loads(payload))
				else:
					jobData[name] = obj

		jobId = await engine.newJob(route, jobData, binaries)
		return {"jobId": jobId}
	
	# Change the function signature with expected types from the api description so that the api doc is correctly generated
	params = []
	if type(body) is dict:
		model = pydantic.create_model(route + "Body", **body)
		params.append(Parameter("data", kind=Parameter.POSITIONAL_ONLY, annotation=model))
	elif type(body) is str:
		params.append(Parameter(body, kind=Parameter.POSITIONAL_ONLY, annotation=UploadFile))
	elif type(body) is list:
		for name in body:
			params.append(Parameter(name, kind=Parameter.POSITIONAL_ONLY, annotation=UploadFile))
	params.append(Parameter("req", kind=Parameter.POSITIONAL_ONLY, annotation=Request))
	handler.__signature__ = Signature(params)

	app.add_api_route("/services/" + route, handler, methods=["POST"],  response_model=interface.JobResponse, summary=summary, description=description)
	# Force the regeneration of the schema
	app.openapi_schema = None

async def startup():
	timer.start()

async def shutdown():
	timer.stop()

app = FastAPI(on_startup=[startup], on_shutdown=[shutdown])
registry = Registry.Registry("/tmp/registry")
engine = Engine.Engine(
	registry,
	os.environ["APP_ENGINE"] if "APP_ENGINE" in os.environ else None,
	os.environ["APP_EXTERNAL_URL"] if "APP_EXTERNAL_URL" in os.environ else None)
timer = Cron.Timer(
	timeout=int(os.environ["APP_CRON"]) if "APP_CRON" in os.environ else 300,
	callback=engine.clean,
	delta=datetime.timedelta(seconds=int(os.environ["APP_LIFESPAN"]) if "APP_LIFESPAN" in os.environ else 1800))

@app.get("/tasks/{taskId}", summary="Get results of a task")
def getTaskResult(taskId: str):
	result = engine.getResult(taskId)
	return JSONResponse(result)

@app.get("/tasks/{taskId}/status", summary="Get the status of a task")
def getTaskStatus(taskId: str):
	status = engine.pollTask(taskId)
	return {"id": taskId, "status": status}

@app.get("/tasks/{taskId}/raw", summary="Get raw pipeline data for a task")
def getTaskRaw(taskId: str):
	raw = engine.getJobRaw(taskId)
	return JSONResponse(raw)

@app.get("/tasks/{taskId}/files/{fileName}", summary="Retrieve a binary result of a task")
def getTaskResultFile(taskId: str, fileName: str):
	stream = engine.getResultFile(taskId, fileName)
	return StreamingResponse(stream, media_type="application/octet-stream")

@app.post("/services", summary="Create a new service or pipeline")
def createService(service: Union[interface.ServiceDescription, interface.PipelineDescription]):
	if service.type is interface.ServiceType.SERVICE:
		api = service.api.dict()
		serviceName = api["route"]
		if serviceName not in engine.endpoints:
			engine.createServicePipeline(service.url, api)
			addRoute(**api)
	elif service.type is interface.ServiceType.PIPELINE:
		api = engine.addPipeline(service.dict())
		addRoute(**api)

@app.get("/stats", summary="Get engine and pipelines statistics")
def getTaskRaw():
	stats = engine.getStats()
	return JSONResponse(stats)

@app.delete("/services/{serviceName}", summary="Remove a service or pipeline")
def removeService(serviceName: str):
	if serviceName in engine.endpoints:
		engine.removePipeline(serviceName)
		for i in range(len(app.routes)):
			if app.routes[i].path == "/services/" + serviceName:
				app.routes.pop(i)
				break
		# Force the regeneration of the schema
		app.openapi_schema = None

@app.post("/processing", include_in_schema=False)
async def processCallback(task_id: str, request: Request):
	data = {}
	binaries = []
	
	contentType = request.headers["content-type"].replace(";", "")

	if "application/json" in contentType:
		data.update(await request.json())
	elif "multipart/form-data" in contentType:
		form = await request.form()
		for k in form:
			obj = form[k]
			if obj.content_type == "application/json":
				payload = await obj.read()
				data.update(json.loads(payload))
			else:
				data[k] = obj
				binaries.append(k)

	await engine.processTask(task_id, data, binaries)
