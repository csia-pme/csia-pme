import asyncio

class Timer:
	def __init__(self, timeout, callback, **kwargs):
		self.timeout = timeout
		self.callback = callback
		self.kwargs = kwargs
		self.task = None

	def start(self):
		self.task = asyncio.ensure_future(self.job())

	async def job(self):
		while True:
			await asyncio.sleep(self.timeout)
			await self.callback(**self.kwargs)

	def stop(self):
		self.task.cancel()
