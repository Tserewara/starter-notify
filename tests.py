import json
import os
import time
import urllib.request

BASE = os.environ.get("API_URL", "http://api:8000")


def request(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


request("POST", "/_reset")
result = request("POST", "/notifications", {"channel": "email", "body": "welcome"})
for _ in range(40):
    status = request("GET", "/notifications/" + result["id"])
    if status["status"] == "delivered":
        break
    time.sleep(0.05)
assert status["status"] == "delivered"
print("2 tests passed")

