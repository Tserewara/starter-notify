.PHONY: up down test notify metrics provider-outage
up:
	docker compose up -d --build
down:
	docker compose down -v
test:
	docker compose run --rm api python3 /app/tests.py
notify:
	docker compose exec -T api python3 /app/loadgen.py
metrics:
	curl -s http://localhost:58002/metrics
provider-outage:
	curl -s -X POST http://localhost:58001/_control -H 'content-type: application/json' -d '{"fail":true}'

