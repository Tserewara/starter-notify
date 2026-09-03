import json
import os
import threading
import time
import uuid

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


def new_redis():
    return redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)


class Notification(BaseModel):
    user_id: str = "user-1"
    channel: str
    body: str = Field(min_length=1)
    urgency: str = "normal"


api_app = FastAPI(title="Bellbird notifications")
provider_app = FastAPI(title="Bellbird fake provider")
provider_state = {"latency_ms": 40, "fail": False, "calls": 0}
provider_lock = threading.Lock()


@api_app.get("/health")
def api_health():
    new_redis().ping()
    return {"ok": True}


@api_app.post("/notifications", status_code=202)
def enqueue(notification: Notification):
    notification_id = str(uuid.uuid4())
    record = notification.model_dump() | {"id": notification_id, "queued_at": time.time()}
    r = new_redis()
    r.hset(f"notification:{notification_id}", mapping={"record": json.dumps(record), "status": "queued"})
    r.rpush("notification_queue", json.dumps(record))
    return {"id": notification_id, "status": "queued"}


@api_app.get("/notifications/{notification_id}")
def notification_status(notification_id: str):
    values = new_redis().hgetall(f"notification:{notification_id}")
    if not values:
        raise HTTPException(status_code=404, detail="notification not found")
    result = json.loads(values["record"])
    result["status"] = values.get("status")
    if "delivered_at" in values:
        result["delivered_at"] = float(values["delivered_at"])
        result["delivery_ms"] = round((result["delivered_at"] - result["queued_at"]) * 1000, 1)
    if "error" in values:
        result["error"] = values["error"]
    return result


@api_app.post("/_reset")
def reset():
    r = new_redis()
    for key in r.scan_iter("notification:*"):
        r.delete(key)
    r.delete("notification_queue", "notification_dlq", "notification_events")
    r.delete("provider_calls")
    return {"ok": True}


@api_app.get("/metrics")
def metrics():
    r = new_redis()
    delivered = 0
    lost = 0
    delivery_ms = []
    for key in r.scan_iter("notification:*"):
        values = r.hgetall(key)
        if values.get("status") == "delivered":
            delivered += 1
            if json.loads(values["record"]).get("channel") == "push":
                delivery_ms.append(float(values.get("delivery_ms", 0)))
        if values.get("status") == "lost":
            lost += 1
    delivery_ms.sort()
    p95 = delivery_ms[min(len(delivery_ms) - 1, int(len(delivery_ms) * 0.95))] if delivery_ms else 0
    return {"delivered": delivered, "lost": lost, "queue_depth": r.llen("notification_queue"), "dlq": r.llen("notification_dlq"), "provider_calls": int(r.get("provider_calls") or 0), "otp_p95_ms": p95}


@provider_app.post("/_control")
def provider_control(payload: dict):
    with provider_lock:
        if "latency_ms" in payload:
            provider_state["latency_ms"] = int(payload["latency_ms"])
        if "fail" in payload:
            provider_state["fail"] = bool(payload["fail"])
    return provider_state


@provider_app.post("/send")
def provider_send(payload: dict):
    with provider_lock:
        latency_ms = provider_state["latency_ms"]
        fail = provider_state["fail"]
        provider_state["calls"] += 1
    time.sleep(latency_ms / 1000)
    if fail:
        raise HTTPException(status_code=503, detail="provider outage")
    return {"accepted": True, "provider_calls": provider_state["calls"]}


@provider_app.get("/health")
def provider_health():
    return {"ok": True}
