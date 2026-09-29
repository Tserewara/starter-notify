"""Last month, small: fifteen newsletters queued, then one urgent login code.

Waits until the provider has all sixteen (or 60 seconds pass) and prints
how many arrived and how long the code took from being accepted to reaching
the provider.
"""

import time

from common import PROVIDER, call, received_ids, send

call("POST", f"{PROVIDER}/_control", {"fail": False, "latency_ms": 40})
call("DELETE", f"{PROVIDER}/received")
ids = [send({"channel": "email", "body": f"newsletter-{n}", "urgency": "low", "user_id": f"user-{n}"})[0]
       for n in range(15)]
otp_id, otp_accepted = send({"channel": "push", "body": "your code is 482913", "urgency": "urgent", "user_id": "user-1"})
ids.append(otp_id)

deadline = time.time() + 60
while time.time() < deadline:
    got = received_ids()
    if all(i in got for i in ids):
        break
    time.sleep(0.05)
got = received_ids()
otp = got.get(otp_id)
otp_ms = f"{(otp['received_at'] - otp_accepted) * 1000:.0f}" if otp else "never"
position = sorted(got.values(), key=lambda r: r["received_at"]).index(otp) + 1 if otp else "-"
print(f"sent=16 delivered={sum(1 for i in ids if i in got)} otp_position={position} otp_ms={otp_ms}", flush=True)
