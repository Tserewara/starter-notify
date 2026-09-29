"""The provider goes down: five notifications are accepted while it fails,
and it comes back some seconds later (2 by default, `outage.py 10` for a
long one).

Waits up to 90 seconds for every one of the five to be accounted for, then
prints the outcome. A notification is accounted for when the provider got
it, or when the service reports it `dead_lettered` (given up on, kept for
an operator). Anything else is lost.
"""

import sys
import time

from common import PROVIDER, call, received_ids, send, status

call("DELETE", f"{PROVIDER}/received")
call("POST", f"{PROVIDER}/_control", {"fail": True, "latency_ms": 40})
ids = [send({"channel": "email", "body": f"order update {n}", "urgency": "normal", "user_id": f"user-{n}"})[0]
       for n in range(5)]
time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 2)
call("POST", f"{PROVIDER}/_control", {"fail": False})

deadline = time.time() + 90
while time.time() < deadline:
    got = received_ids()
    pending = [i for i in ids if i not in got and status(i) != "dead_lettered"]
    if not pending:
        break
    time.sleep(0.2)
got = received_ids()
delivered = sum(1 for i in ids if i in got)
dead = sum(1 for i in ids if i not in got and status(i) == "dead_lettered")
print(f"accepted=5 delivered={delivered} dead_lettered={dead} lost={5 - delivered - dead}", flush=True)
