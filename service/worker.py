"""The delivery worker: takes notifications off the queue in order and hands
each one to the provider."""

import json
import os
import time
import urllib.error
import urllib.request

import redis

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
PROVIDER_URL = os.environ["PROVIDER_URL"]


def send(record):
    request = urllib.request.Request(PROVIDER_URL + "/send", data=json.dumps(record).encode(),
                                     method="POST", headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def work():
    while True:
        item = r.blpop("notification_queue", timeout=2)
        if not item:
            continue
        record = json.loads(item[1])
        key = f"notification:{record['id']}"
        try:
            send(record)
            r.hset(key, mapping={"status": "delivered", "delivered_at": time.time()})
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            r.hset(key, mapping={"status": "failed", "error": str(exc)})


if __name__ == "__main__":
    work()
