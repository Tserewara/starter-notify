"""The notification service's given behaviour, black-box over HTTP. A port passes these."""

import os
import time
import unittest

import httpx

SERVICE = os.environ.get("SERVICE_URL", "http://localhost:58002")
PROVIDER = os.environ.get("PROVIDER_URL", "http://localhost:58001")


class Contract(unittest.TestCase):
    def setUp(self):
        httpx.post(f"{PROVIDER}/_control", json={"fail": False, "latency_ms": 40})

    def test_health(self):
        self.assertEqual(httpx.get(f"{SERVICE}/health").status_code, 200)

    def test_accepted_then_delivered_to_the_provider(self):
        r = httpx.post(f"{SERVICE}/notifications", json={"channel": "email", "body": "welcome", "user_id": "user-7"})
        self.assertEqual(r.status_code, 202)
        notification_id = r.json()["id"]
        self.assertEqual(r.json()["status"], "queued")
        for _ in range(100):
            if httpx.get(f"{SERVICE}/notifications/{notification_id}").json()["status"] == "delivered":
                break
            time.sleep(0.05)
        record = httpx.get(f"{SERVICE}/notifications/{notification_id}").json()
        self.assertEqual(record["status"], "delivered")
        self.assertEqual(record["id"], notification_id)
        received = {x["id"]: x for x in httpx.get(f"{PROVIDER}/received").json()}
        self.assertIn(notification_id, received)
        self.assertEqual(received[notification_id]["channel"], "email")

    def test_invalid_notification_is_422(self):
        r = httpx.post(f"{SERVICE}/notifications", json={"channel": "email", "body": ""})
        self.assertEqual(r.status_code, 422)

    def test_unknown_notification_is_404(self):
        self.assertEqual(httpx.get(f"{SERVICE}/notifications/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
