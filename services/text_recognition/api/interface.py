from pydantic import BaseModel

_uid = 0


def uid():
    global _uid
    _uid += 1
    return _uid


class TaskId(BaseModel):
    task_id: str


# if the service has only one route
engineAPI = {
        "image-to-text": {
            "route": "image-to-text", 
            "body": ["language", "image"],
            "bodyType": ["text/plain", "[image/png, image/jpeg]"],
            "resultType": ["application/json"],
            "summary": "Returns the text in an image"
        },
        "image-to-pdf": {
            "route": "image-to-pdf", 
            "body": ["language", "image"],
            "bodyType": ["text/plain", "[image/png, image/jpeg]"],
            "resultType": ["application/pdf"],
            "summary": "Returns a PDF with the recognized text selectable from an image"
        },
        "image-to-data": {
            "route": "image-to-data", 
            "body": ["language", "image"],
            "bodyType": ["text/plain", "[image/png, image/jpeg]"],
            "resultType": ["application/json"],
            "summary": "Returns the meta-data of recognized text in an image"
        },

    }
