import json
import os
import time
import urllib.error
import urllib.request

import redis

R = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
PROVIDER_URL = os.environ["PROVIDER_URL"]


def send(record):
    body = json.dumps(record).encode()
    request = urllib.request.Request(PROVIDER_URL + "/send", data=body, method="POST", headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def work():
    while True:
        item = R.blpop("notification_queue", timeout=2)
        if not item:
            continue
        record = json.loads(item[1])
        key = f"notification:{record['id']}"
        try:
            send(record)
            delivered_at = time.time()
            delivery_ms = round((delivered_at - record["queued_at"]) * 1000, 1)
            R.hset(key, mapping={"status": "delivered", "delivered_at": delivered_at, "delivery_ms": delivery_ms})
            R.incr("provider_calls")
            R.rpush("notification_events", json.dumps({"id": record["id"], "at": delivered_at}))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            R.hset(key, mapping={"status": "lost", "error": str(exc)})


if __name__ == "__main__":
    work()
