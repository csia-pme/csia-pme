import asyncio
import httpx
import logging
from io import BytesIO

class Worker():
	def __init__(self):
		self.asyncTask = None
		self.running = False
		self.queue = asyncio.Queue()
		self.next = None

	def start(self):
		self.running = True
		self.asyncTask = asyncio.create_task(self.run())

	def chain(self, worker):
		self.next = worker

	async def stop(self):
		self.running = False
		await self.queue.put(None)
		await self.asyncTask

	async def addTask(self, task):
		await self.queue.put(task)

	async def run(self):
		while self.running:
			task = await self.queue.get()
			if task is not None:
				result = await self.process(task)
				if result is not None and self.next is not None:
					await self.next.addTask(result)

	async def post_request_to_endpoint(self , task):
		params = {
			"language": (await task["language"].read()).decode("utf-8")
		}

		file = {
			"image": (
				task["image"].filename,
				task["image"].file,
				#task["image"].content_type
				"image/png" # Due to engine not sending MIME
				)
			}

		return httpx.post(f"https://icoservices.kube.isc.heia-fr.ch/text-recognition/{task['operation']}", files=file, params=params)
	
	async def process(self, task):
		try:
			if task["operation"] == "image-to-pdf":
				task["result"] = (await self.post_request_to_endpoint(task)).content
			elif task["operation"] == "image-to-data":
				task["result"] = {"result": (await self.post_request_to_endpoint(task)).json()} # Due to bug in engine with tables in top level
			elif task["operation"] == "image-to-text":
				task["result"] = (await self.post_request_to_endpoint(task)).json()
		except Exception as e:
			task["error"] = "Failed to process image: " + str(e)

		return task

class Callback(Worker):
	def __init__(self):
		super().__init__()
		self.client = httpx.AsyncClient(timeout=30.0)

	async def process(self, task):
		url = task["callback_url"]
		task_id = task["task_id"]
		if url is not None:
			res = task["result"] if "result" in task else None
			try:
				if "error" in task:
					data = {"type": "error", "message": task["error"]}
					await self.client.post(url, params={"task_id": task_id}, json=data)
				elif type(res) is dict:
					await self.client.post(url, params={"task_id": task_id}, json=res)
				elif type(res) is bytes:
					await self.client.post(url, params={"task_id": task_id}, files={"result": res})
			except Exception as e:
				logging.getLogger("uvicorn").warning("Failed to send back result (" + url + "): " + str(e))
