import asyncio
import httpx
import datetime

from .Pipeline import Pipeline
from .Enums import Status, ServiceType, NodeType, TaskType
from .Errors import ItemNotFound, BadStatus, Duplicate


class Engine():
    def __init__(self, registry, route, externalRoute):
        self.registry = registry
        self.route = route
        self.externalRoute = externalRoute
        self.client = httpx.AsyncClient()
        self.endpoints = {}
        self.api = {}

        # Worker
        self.asyncTask = None
        self.running = False
        self.messages = asyncio.Queue()

    def start(self):
        self.running = True
        self.asyncTask = asyncio.create_task(self.run())

    async def stop(self):
        self.running = False
        await self.messages.put(None)
        await self.asyncTask

    async def run(self):
        while self.running:
            msg = await self.messages.get()
            if msg is not None:
                taskType = msg[0]
                task = msg[1:]
                if taskType == TaskType.ERROR:
                    await self._processError(*task)
                elif taskType == TaskType.PROCESS:
                    await self._processTask(*task)
                elif taskType == TaskType.RETRY:
                    await self._processRetry(*task)

    async def load(self):
        pipelines = await self.registry.getPipelines()
        for pipeline in pipelines:
            endpoint = Pipeline.api(pipeline)["route"]
            if endpoint is not None:
                self.endpoints[endpoint] = str(pipeline["_id"])
                self.api[endpoint] = Pipeline.api(pipeline)

    async def addPipeline(self, pipeline):
        pipeline["timestamp"] = datetime.datetime.utcnow().isoformat()
        api = Pipeline.api(pipeline)
        endpoint = api["route"]
        if endpoint in self.endpoints:
            raise Duplicate("Pipeline already exists for endpoint {endpoint}".format(endpoint=endpoint))
        pid = await self.registry.addPipeline(pipeline)
        if endpoint is not None:
            self.endpoints[endpoint] = pid
            self.api[endpoint] = api
        return api

    async def removePipeline(self, endpoint):
        if endpoint not in self.endpoints:
            raise ItemNotFound("Pipeline {endpoint} not found".format(endpoint=endpoint))
        pid = self.endpoints[endpoint]
        await self.registry.removePipeline(pid)
        self.endpoints.pop(endpoint)
        self.api.pop(endpoint)

    async def newJob(self, endpoint, data, binaries=[]):
        if endpoint not in self.endpoints:
            raise ItemNotFound("Pipeline {endpoint} not found".format(endpoint=endpoint))

        pipelineId = self.endpoints[endpoint]
        pipelineTemplate = await self.registry.getPipeline(pipelineId)
        job = Pipeline.build(pipelineTemplate["nodes"], pipelineId)
        job.node(job.entry).before()
        await self.registry.saveJob(job)
        taskId = await self.registry.addTask({"job": job._id, "node": job.entry})
        requestId = await self.registry.addTask({"job": job._id})
        await self.processTask(taskId, data, binaries)
        return requestId

    async def processError(self, taskId, message):
        await self.messages.put([TaskType.ERROR, taskId, message])

    async def _processError(self, taskId, message):
        task = await self.registry.popTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))

        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        job.status = Status.ERROR
        job.error = message
        job.touch()
        await self.registry.saveJob(job)

    async def processRetry(self, taskId):
        await self.messages.put([TaskType.RETRY, taskId])

    async def _processRetry(self, taskId):
        task = await self.registry.getTask(taskId)
        job = await self.registry.getJob(task["job"])
        if job is None:
            return

        if job.status != Status.RUNNING:
            return

        job.hide("_engine", self)
        nodeId = task["node"]
        retryNode = job.node(nodeId)

        for i in range(len(job.retries)):
            if job.retries[i] == (nodeId, taskId):
                job.retries.pop(i)
                break

        await retryNode.process(taskId)
        job.touch()
        await self.registry.saveJob(job)

    async def processTask(self, taskId, data, binaries=[]):
        await self.messages.put([TaskType.PROCESS, taskId, data, binaries])

    async def _processTask(self, taskId, data, binaries=[]):
        task = await self.registry.popTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))

        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        if job.status != Status.RUNNING:
            return

        job.hide("_engine", self)
        nodeId = task["node"]
        finishedNode = job.node(nodeId)

        # Process binary input if any
        for binary in binaries:
            stream = data[binary]
            binUid = await self.registry.storeBinary(stream)
            data[binary] = binUid
            job.binaries[str.join(".", [nodeId, "out", binary])] = binUid

        finishedNode.finished = True
        finishedNode.after(data)

        # Refactor this?!
        toProcess = []

        for nextId in finishedNode.next:
            succ = job.node(nextId)
            if succ.ready():
                succ.before()
                taskId = await self.registry.addTask({"job": job._id, "node": nextId})
                toProcess.append((succ, taskId))

        if finishedNode.type == NodeType.END:
            job.status = Status.FINISHED

        job.touch()
        await self.registry.saveJob(job)

        # Refactor this?!
        for item in toProcess:
            node, taskId = item
            await node.process(taskId)
            job.touch()
            await self.registry.saveJob(job)

    async def pollTask(self, taskId):
        task = await self.registry.getTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))
        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        status = {"status": job.status}
        if job.status == Status.ERROR:
            status["message"] = job.error
        return status

    async def getResult(self, taskId):
        task = await self.registry.getTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))

        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        if job.status != Status.FINISHED:
            raise BadStatus("Pipeline is not finished ({status})".format(status=job.status))

        out = job.node(job.end).out
        for key in job.node(job.end).out:
            identifier = str.join(".", [job.end, "out", key])
            if identifier in job.binaries:
                out[key] = "{engine}/tasks/{taskId}/files/{name}".format(engine=self.externalRoute, taskId=taskId,
                                                                         name=key)
        return out

    async def getResultFile(self, taskId, fileName):
        task = await self.registry.getTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))

        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        if job.status != Status.FINISHED:
            raise BadStatus("Pipeline is not finished ({status})".format(status=job.status))

        identifier = str.join(".", [job.end, "out", fileName])

        if identifier not in job.binaries:
            raise ItemNotFound("No file named " + fileName + " for task " + taskId)

        binUid = job.binaries[identifier]
        return await self.registry.getBinaryStream(binUid)

    async def getJobRaw(self, taskId):
        task = await self.registry.getTask(taskId)
        if task is None:
            raise ItemNotFound("Task {taskId} not found".format(taskId=taskId))

        job = await self.registry.getJob(task["job"])
        if job is None:
            raise ItemNotFound("Job for task {taskId} not found".format(taskId=taskId))

        return job.data

    async def createServicePipeline(self, url, api):
        name = api["route"]

        entry = {"type": NodeType.ENTRY, "id": name + "-entry", "api": api, "next": [name + "-component"]}
        component = {"type": NodeType.SERVICE, "id": name + "-component", "url": url, "next": [name + "-end"]}
        end = {"type": NodeType.END, "id": name + "-end"}

        pipeline = {"type": ServiceType.SERVICE, "nodes": [entry, component, end]}
        await self.addPipeline(pipeline)

    async def clean(self, delta):
        now = datetime.datetime.utcnow()
        for job in await self.registry.getAllJobs():
            if now - job.timestamp() > delta:
                binUids = set([job.binaries[binary] for binary in job.binaries])
                for binUid in binUids:
                    await self.registry.removeBinary(binUid)
                await self.registry.removeJob(job._id)

    async def retry(self):
        now = datetime.datetime.utcnow()
        tasksToRetry = []
        for job in await self.registry.getAllJobs():
            if job.status == Status.RUNNING and len(job.retries) > 0:
                for nodeId, taskId in job.retries:
                    node = job.node(nodeId)
                    retryDT = datetime.datetime.fromisoformat(node.nextRetry)
                    if now >= retryDT:
                        tasksToRetry.append(taskId)

        for taskId in tasksToRetry:
            await self.processRetry(taskId)

    async def getStats(self):
        # Reverse id to endpoints
        models = {}
        for e in self.endpoints:
            pid = self.endpoints[e]
            models[pid] = e

        endpoints = dict.fromkeys(self.endpoints, 0)
        undef = 0

        running = 0
        finished = 0
        failed = 0

        jobs = await self.registry.getAllJobs()
        for job in jobs:
            if job.status == Status.RUNNING:
                running += 1
            elif job.status == Status.FINISHED:
                finished += 1
            elif job.status == Status.ERROR:
                failed += 1

            eid = job.model
            if eid in models:
                endpoint = models[eid]
                endpoints[endpoint] += 1
            else:
                undef += 1

        if undef > 0:
            endpoints["UNDEFINED"] = undef

        stats = {}
        stats["jobs"] = {"total": len(jobs), "running": running, "finished": finished, "failed": failed}
        stats["services"] = endpoints

        return stats

    async def getPipelines(self):
        pipelines = await self.registry.getPipelines()
        return list(pipelines)

    async def getPipeline(self, name):
        if name not in self.endpoints:
            raise ItemNotFound("Pipeline {name} not found".format(name=name))
        pipelineId = self.endpoints[name]
        pipelineTemplate = await self.registry.getPipeline(pipelineId)
        return pipelineTemplate

    async def touchPipeline(self, name):
        await self.registry.updatePipeline(self.endpoints[name], "timestamp", datetime.datetime.utcnow().isoformat())
