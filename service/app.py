import json
import os
import time
import uuid

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
app = FastAPI(title="Bellbird notifications")


class Notification(BaseModel):
    user_id: str = "user-1"
    channel: str
    body: str = Field(min_length=1)
    urgency: str = "normal"


@app.get("/health")
def health():
    r.ping()
    return {"ok": True}


@app.post("/notifications", status_code=202)
def enqueue(notification: Notification):
    notification_id = str(uuid.uuid4())
    record = notification.model_dump() | {"id": notification_id, "queued_at": time.time()}
    r.hset(f"notification:{notification_id}", mapping={"record": json.dumps(record), "status": "queued"})
    r.rpush("notification_queue", json.dumps(record))
    return {"id": notification_id, "status": "queued"}


@app.get("/notifications/{notification_id}")
def notification_status(notification_id: str):
    values = r.hgetall(f"notification:{notification_id}")
    if not values:
        raise HTTPException(status_code=404, detail="notification not found")
    result = json.loads(values["record"])
    result["status"] = values["status"]
    if "delivered_at" in values:
        result["delivery_ms"] = round((float(values["delivered_at"]) - result["queued_at"]) * 1000, 1)
    if "error" in values:
        result["error"] = values["error"]
    return result
