import json
import os
import time
import urllib.request

BASE = os.environ.get("API_URL", "http://api:8000")
PROVIDER = os.environ.get("PROVIDER_URL", "http://provider:8001")


def request(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def wait_for(count, key):
    for _ in range(100):
        data = request("GET", BASE + "/metrics")
        if data[key] >= count:
            return data
        time.sleep(0.05)
    return request("GET", BASE + "/metrics")


def main():
    request("POST", BASE + "/_reset")
    request("POST", PROVIDER + "/_control", {"fail": False, "latency_ms": 40})
    for index in range(15):
        request("POST", BASE + "/notifications", {"channel": "email", "body": f"newsletter-{index}", "urgency": "low"})
    request("POST", BASE + "/notifications", {"channel": "push", "body": "one-time code", "urgency": "urgent"})
    print(json.dumps(wait_for(16, "delivered")))


if __name__ == "__main__":
    main()

