import asyncio
import httpx
import logging

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

	async def image_to_text(task):

	# TODO: implement this method to process the task of the service
	async def process(self, task):
		try:
			if task["operation"] == 'image-to-text':
				pass
			if task["operation"] == 'image-to-pdf':
				pass
			if task["operation"] == 'image-to-data':
				pass

			task["result"] = {"result": task["operation"]}
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
			data = None
			if "error" in task:
				data = {"type": "error", "message": task["error"]}
			else:
				data = task["result"]
			try:
				await self.client.post(url, params={"task_id": task_id}, json=data)
			except Exception as e:
				logging.getLogger("uvicorn").warning("Failed to send back result (" + url + "): " + str(e))
