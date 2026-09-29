import json
import os
import time
import urllib.request

SERVICE = os.environ.get("SERVICE_URL", "http://service:8000")
PROVIDER = os.environ.get("PROVIDER_URL", "http://provider:8001")


def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def send(payload):
    """POST a notification; returns its id and the moment the service accepted it."""
    accepted = call("POST", f"{SERVICE}/notifications", payload)
    return accepted["id"], time.time()


def received_ids():
    return {r["id"]: r for r in call("GET", f"{PROVIDER}/received")}


def status(notification_id):
    return call("GET", f"{SERVICE}/notifications/{notification_id}").get("status")
