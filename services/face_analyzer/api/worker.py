import asyncio
import httpx
import io
import logging
from deepface import DeepFace
from PIL import Image
import numpy as np

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

	async def process(self, task):
		try:
			raw = await task["image"].read()
			buff = io.BytesIO(raw)
			img_pil = Image.open(buff)
			img = np.array(img_pil)
			diagnos = DeepFace.analyze(img_path=img, actions=['age', 'gender', 'race', 'emotion'], enforce_detection=True, detector_backend="retinaface", prog_bar=False)
			task["result"] = diagnos
		except ValueError:
			task["result"] = {}
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
