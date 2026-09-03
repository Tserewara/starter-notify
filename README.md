# Bellbird notifications

Bellbird sends marketplace notifications through push, email, SMS, and in-app channels. The local lab has an API, a Redis-backed queue, one worker, and fake providers whose latency and failure mode can be changed while the services run.

## Run

You need Docker with Compose. Run `make up`, then `make test`. The API is at `http://localhost:58002`; the provider control API is at `http://localhost:58001`.

`make notify` queues fifteen email newsletters followed by one urgent push notification and prints delivery metrics. `POST /_control` on the provider accepts `{"latency_ms": 250}` or `{"fail": true}`. The API's `/metrics` endpoint reports queue depth, deliveries, lost notifications, the dead-letter list length, provider calls, and push p95 delivery time.

The starter keeps the queue and delivery record in Redis. `make down` removes the local volume.

## License

MIT. See `LICENSE`.

