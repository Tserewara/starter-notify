COMPOSE = docker compose -f harness/compose.yaml
.PHONY: up down contract notify outage outage-long provider-down provider-up provider-slow received logs

# The notification service, Redis and the fake provider.
up:
	$(COMPOSE) up -d --build --wait service provider

down:
	$(COMPOSE) down -v

# What the service already does, black-box. Passes before and after your change.
contract:
	$(COMPOSE) run --rm --build contract

# Fifteen newsletters, then one urgent login code. One summary line.
notify:
	$(COMPOSE) run --rm --build tools python3 notify.py

# The provider fails while five notifications are accepted, and comes back two seconds later.
outage:
	$(COMPOSE) run --rm --build tools python3 outage.py 2

# The same, with the provider down for ten seconds.
outage-long:
	$(COMPOSE) run --rm --build tools python3 outage.py 10

provider-down:
	curl -fsS -X POST http://localhost:58001/_control -H 'content-type: application/json' -d '{"fail": true}'; echo
provider-up:
	curl -fsS -X POST http://localhost:58001/_control -H 'content-type: application/json' -d '{"fail": false}'; echo
# Every send takes 250 ms instead of 40.
provider-slow:
	curl -fsS -X POST http://localhost:58001/_control -H 'content-type: application/json' -d '{"latency_ms": 250}'; echo

# What the provider has accepted so far.
received:
	@curl -fsS http://localhost:58001/received; echo

logs:
	$(COMPOSE) logs -f service
